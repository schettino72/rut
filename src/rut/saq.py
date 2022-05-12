from __future__ import annotations

"""subprocess async queue


Application protocol for Master / Worker based.

Master can handles multiple workers.
Jobs are dispatched one by one to available (READY) workers.
Workers run in blocking mode, can receive only on JOB at a time.

The protocol consists of:
  - Header: fixed length 5 bytes
    - MessageType: 1 byte unsigned char (B)
    - Payload length: 4 bytes unsigned int (I), network, big-endian (!)
  - Payload: variable length using msgpack
"""

from typing import Any, AsyncIterator
import struct
import asyncio

import msgpack  # type: ignore



# python struct format:  char(MessageType) + unsigned int(payload length)
MSG_FORMAT = '!BI'

class MessageType:
    # master  -> worker
    JOB = 1   # master  -> worker: content is job instruction
    # for worker as subprocess no message is sent, it relies on stdin being closed
    STOP = 2  # TODO: signal worker to stop (after current job)

    # worker ->  master
    DATA = 101    # status/result of job being done
    READY = 102  # JOB is done, instruct master to send another job
    DONE = 103   # JOB is done, instruct master to send another job


class Worker:
    """Manages communication on worker process"""

    def __init__(self, instream, outstream):
        self.instream = instream
        self.outstream = outstream

    def send_msg(self, payload: bytes):
        """send application message"""
        self.outstream.write(struct.pack(MSG_FORMAT, MessageType.DATA, len(payload)))
        self.outstream.write(payload)
        self.outstream.flush()

    def send_ctl(self, msg_type: int):
        """send a meta/control message i.e READY, DONE"""
        self.outstream.write(struct.pack(MSG_FORMAT, msg_type, 0))
        self.outstream.flush()

    def read_one(self) -> tuple[int, Any]:
        """receive message from master"""
        header_data = self.instream.read(5)
        if not header_data:
            raise EOFError('Worker process stdin has no more data.')
        msg_type, payload_len = struct.unpack(MSG_FORMAT, header_data)
        msg = msgpack.unpackb(self.instream.read(payload_len))
        return msg_type, msg

    def recv_data(self):
        """higher level generator to iterate only through received data."""
        while True:
            try:
                msg_type, msg = self.read_one()
            except EOFError:
                self.send_ctl(MessageType.DONE)
                break
            assert msg_type == MessageType.JOB
            yield msg
            # signal worker is ready to receive next task
            self.send_ctl(MessageType.READY)



class WorkerManager:
    """Manages a worker from master process

    - STDOUT must receive ONLY msgpack data
    """
    def __init__(self, name, process, detail=None):
        self.name = name
        self.detail = detail
        self.process = process
        self.running = True  # worker process not terminated yet
        self._read_stdout: asyncio.Task[str] = None

    async def _read_pack(self):
        """read msgpack stream"""
        stream = self.process.stdout
        header_data = await stream.readexactly(5)
        if not header_data:
            return None, None  # EOF
        msg_type, payload_len = struct.unpack(MSG_FORMAT, header_data)
        if payload_len:
            payload = await stream.readexactly(payload_len)
            msg = msgpack.unpackb(payload)
        else:
            msg = b''
        return msg_type, msg

    @property
    def create_read_task(self):
        """GET or create task/awaitable for StreamReader"""
        if not self._read_stdout:
            self._read_stdout = asyncio.create_task(self._read_pack(), name=self.name)
        return self._read_stdout

    def get_data(self):
        """must be called only if it known that read_task has a result"""
        msg_type, data = self._read_stdout.result()
        self._read_stdout = None
        return msg_type, data


    def _write_pack(self, msg_type, payload):
        transport = self.process.stdin._transport
        transport.write(struct.pack(MSG_FORMAT, msg_type, len(payload)))
        transport.write(payload)

    def send_job(self, data):
        payload = msgpack.packb(data)
        self._write_pack(MessageType.JOB, payload)



class Master:
    """Manages multiple worker processes

    - exec()
    """
    def __init__(self):
        self.workers: dict[str: WorkerManager] = {}

    async def exec(self, name: str, command: str) -> WorkerManager:
        """Create subprocess and wrap into WorkerManager"""
        proc = await asyncio.create_subprocess_exec(
            *command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            # stderr=asyncio.subprocess.PIPE,
        )
        worker = WorkerManager(name, proc, detail=command)
        self.workers[name] = worker
        return worker


    async def recv_worker_msgs(self) -> AsyncIterator[tuple[WorkerManager, int, Any]]:
        """Generator of received messages from worker processes

        Similar to a socket select()
        """
        while wait_for := [w.create_read_task for w in self.workers.values() if w.running]:
            done, _ = await asyncio.wait(wait_for, return_when=asyncio.FIRST_COMPLETED)
            for tdone in done:
                worker = self.workers[tdone.get_name()]
                msg_type, data = worker.get_data()
                if msg_type == MessageType.DONE:
                    worker.running = False
                yield (worker, msg_type, data)
