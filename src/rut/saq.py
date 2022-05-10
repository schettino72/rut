"""subprocess async queue"""


import asyncio
from asyncio import Task
from asyncio import streams
from asyncio import events
from asyncio.subprocess import SubprocessStreamProtocol, Process

import msgpack  # type: ignore

############################################

# streams on the master size
class PackStreamReader(streams.StreamReader):
    """Overwrite to add support for reading msgpack"""
    def __init__(self, limit=streams._DEFAULT_LIMIT, loop=None):
        super().__init__(limit, loop)
        self.unpacker = msgpack.Unpacker()

    async def read_pack(self):
        """read msgpack stream"""
        # check if there are any complete msg from read data
        try:
            return self.unpacker.unpack()
        except msgpack.OutOfData:
            pass
        while True:
            data = await self.read(1024)
            if not data:
                return  # EOF
            self.unpacker.feed(data)
            try:
                return self.unpacker.unpack()
            except msgpack.OutOfData:
                # if not enough data was read for a full msg
                await self._wait_for_data('read_pack')


class PackStreamWriter(streams.StreamWriter):
    # def __init__(self, transport, protocol, reader, loop):
    #     super().__init__(self, transport, protocol, reader, loop)

    def write_pack(self, data):
        self._transport.write(msgpack.packb(data))


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



class Worker:
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
        data = self._read_stdout.result()
        self._read_stdout = None
        if not data:
            self.running = False
        return data

    def write_to_worker(self, data):
        self.process.stdin.write_pack(data)


class ProcessManager:
    def __init__(self):
        self.workers = {}

    async def exec(self, name, command: str):
        proc = await create_subprocess_exec(
            *command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        worker = Worker(name, proc, detail=command)
        self.workers[name] = worker
        return worker

    async def iter_out_msgs(self):
        while wait_for := [w.read_out_task for w in self.workers.values() if w.running]:
            done, _ = await asyncio.wait(wait_for, return_when=asyncio.FIRST_COMPLETED)
            for tdone in done:
                worker = self.workers[tdone.get_name()]
                data = worker.get_data()
                # if data:
                #     data = data.decode('ascii').rstrip()
                yield (worker, data)
