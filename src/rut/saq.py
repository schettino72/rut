from __future__ import annotations

"""subprocess async queue"""

import struct
import asyncio
from asyncio import Task
from asyncio import streams
from asyncio import events
from asyncio.subprocess import SubprocessStreamProtocol, Process

import msgpack  # type: ignore


class MessageType:
    # master  -> worker
    JOB = 1   # master  -> worker: content is job instruction
    # for worker as subprocess no message is sent, it relies on stdin being closed
    STOP = 4  # TODO: signal worker to stop (after current job)

    # worker ->  master
    MSG = 101    # status/result of job being done
    READY = 102  # JOB is done, instruct master to send another job
    DONE = 103   # JOB is done, instruct master to send another job

class Worker:
    """Work message are used for communication between a master/worker

    The protocol consists of:
    - Header: fixed length 5 bytes
      - MessageType: 1 byte unsigned char (B)
      - Payload length: 4 bytes unsigned int (I), network, big-endian (!)
    - Payload: variable length using msgpack
    """
    FORMAT = '!BI'

    def __init__(self, outstream):
        self.outstream = outstream

    def send_msg(self, payload: bytes):
        # payload = msgpack.packb(data)
        self.outstream.write(struct.pack('!BI', MessageType.MSG, len(payload)))
        self.outstream.write(payload)
        self.outstream.flush()

    def send_ctl(self, msg_type):
        self.outstream.write(struct.pack('!BI', msg_type, 0))
        self.outstream.flush()

    @classmethod
    def read_one(cls, in_stream):
        header_data = in_stream.read(5)
        if not header_data:
            return None, None  # no more jobs
        msg_type, payload_len = struct.unpack(cls.FORMAT, header_data)
        msg = msgpack.unpackb(in_stream.read(payload_len))
        return msg_type, msg


############################################

# streams on the master size
class PackStreamReader(streams.StreamReader):
    """Overwrite to add support for reading msgpack"""
    def __init__(self, limit=streams._DEFAULT_LIMIT, loop=None):
        super().__init__(limit, loop)
        self.unpacker = msgpack.Unpacker()

    async def read_pack(self):
        """read msgpack stream"""
        header_data = await self.readexactly(5)
        if not header_data:
            return None, None  # EOF
        msg_type, payload_len = struct.unpack(Worker.FORMAT, header_data)
        if payload_len:
            payload = await self.readexactly(payload_len)
            msg = msgpack.unpackb(payload)
        else:
            msg = b''
        return msg_type, msg


class PackStreamWriter(streams.StreamWriter):
    # def __init__(self, transport, protocol, reader, loop):
    #     super().__init__(self, transport, protocol, reader, loop)

    def write_pack(self, msg_type, payload):
        self._transport.write(struct.pack('!BI', msg_type, len(payload)))
        self._transport.write(payload)


class SubprocessStreamProtocolWithMsgPack(SubprocessStreamProtocol):
    """Overwrite only to use  custom StreamReader class"""
    StreamReaderCls = PackStreamReader
    StreamWriterCls = PackStreamWriter

    def connection_made(self, transport):
        self._transport = transport

        stdout_transport = transport.get_pipe_transport(1)
        if stdout_transport is not None:
            self.stdout = self.StreamReaderCls(limit=self._limit,
                                               loop=self._loop)
            self.stdout.set_transport(stdout_transport)
            self._pipe_fds.append(1)

        stderr_transport = transport.get_pipe_transport(2)
        if stderr_transport is not None:
            self.stderr = self.StreamReaderCls(limit=self._limit,
                                               loop=self._loop)
            self.stderr.set_transport(stderr_transport)
            self._pipe_fds.append(2)

        stdin_transport = transport.get_pipe_transport(0)
        if stdin_transport is not None:
            self.stdin = self.StreamWriterCls(stdin_transport,
                                              protocol=self,
                                              reader=None,
                                              loop=self._loop)


async def create_subprocess_exec(*cmd, stdin=None, stdout=None, stderr=None,
                                 limit=streams._DEFAULT_LIMIT, **kwds):
    loop = events.get_running_loop()
    protocol_factory = lambda: SubprocessStreamProtocolWithMsgPack(
        limit=limit, loop=loop)
    transport, protocol = await loop.subprocess_exec(
        protocol_factory,
        *cmd, stdin=stdin, stdout=stdout,
        stderr=stderr, **kwds)
    return Process(transport, protocol, loop)



class WorkerManager:
    """Manages a worker from master process

    - STDOUT must receive ONLY msgpack data
    """
    def __init__(self, name, process, detail=None):
        self.name = name
        self.detail = detail
        self.process = process
        self.running = True  # worker process not terminated yet
        self._read_stdout: Task[str] = None

    @property
    def read_out_task(self):
        """create task/awaitable for StreamReader"""
        if not self._read_stdout:
            self._read_stdout = asyncio.create_task(
                self.process.stdout.read_pack(), name=self.name)
        return self._read_stdout

    def get_data(self):
        """must be called only if it known that read_task has a result"""
        msg_type, data = self._read_stdout.result()
        self._read_stdout = None
        return msg_type, data

    def send_job(self, data):
        payload = msgpack.packb(data)
        self.process.stdin.write_pack(MessageType.JOB, payload)


class ProcessManager:
    def __init__(self):
        self.workers: dict[str: WorkerManager] = {}

    async def exec(self, name, command: str):
        proc = await create_subprocess_exec(
            *command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        worker = WorkerManager(name, proc, detail=command)
        self.workers[name] = worker
        return worker

    async def iter_out_msgs(self):
        while wait_for := [w.read_out_task for w in self.workers.values() if w.running]:
            done, _ = await asyncio.wait(wait_for, return_when=asyncio.FIRST_COMPLETED)
            for tdone in done:
                worker = self.workers[tdone.get_name()]
                msg_type, data = worker.get_data()
                if msg_type == MessageType.DONE:
                    worker.running = False
                yield (worker, msg_type, data)
