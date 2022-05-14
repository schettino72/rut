from io import BytesIO
from pathlib import Path

from rut import check

from rut import saq


class TestWorker:
    def test_send_msg(self):
        w_out = BytesIO()
        worker = saq.Worker(None, w_out)
        worker.send_msg(b'foo123')
        buffer = w_out.getvalue()
        check(buffer[0]) == saq.MessageType.DATA
        check(buffer[1:5]) == b'\x00\x00\x00\x06'
        check(buffer[5:]) == b'foo123'

    def test_send_ctl(self):
        w_out = BytesIO(b'\x00\x00\x00\x06')
        worker = saq.Worker(None, w_out)
        worker.send_ctl(saq.MessageType.READY)
        buffer = w_out.getvalue()
        check(buffer[0]) == saq.MessageType.READY
        check(buffer[1:]) == b'\x00\x00\x00\x00'

    def test_read_one(self):
        msg1 = b'\x01\x00\x00\x00\x06abc123'
        msg2 = b'\x02\x00\x00\x00\x00'
        w_in = BytesIO(msg1 + msg2)
        worker = saq.Worker(w_in, None)
        type1, got1 = worker.read_one()
        check(type1) == saq.MessageType.JOB
        check(got1) == b'abc123'
        type2, got2 = worker.read_one()
        check(type2) == saq.MessageType.STOP
        check(got2) == b''
        with check.raises(EOFError):
            worker.read_one()

    def test_recv_data(self):
        # load as msgpack
        load1 = b'\xa6abc123'  # 'abc123' 7
        load2 = b'\x92\x01\x02'  # [1,2]   3
        msg1 = b'\x01\x00\x00\x00\x07' + load1
        msg2 = b'\x01\x00\x00\x00\x03' + load2
        w_out = BytesIO()
        worker = saq.Worker(BytesIO(msg1 + msg2), w_out)
        got = [m for m in worker.recv_data()]
        check(got) == ['abc123', [1,2]]
        # worker should send 2x READY + DONE
        MT = saq.MessageType
        expected_types = (MT.READY, MT.READY, MT.DONE)
        expected_sent = b''.join([saq.Message.make_header(t, 0) for t in expected_types])
        check(w_out.getvalue()) == expected_sent


class TestMaster:
    async def test_master(self):
        dumb_worker_fn = str(Path(__file__).parent / 'sample_proj/dumb.py')
        master = saq.Master()
        work_mgr1 = await master.add_worker('t1', f"python {dumb_worker_fn}")
        work_mgr1.send_job(b'one')
        work_mgr2 = await master.add_worker('t2', f"python {dumb_worker_fn}")
        work_mgr2.send_job('two')
        got = {'t1': [], 't2': []}
        async for mgr, msg_type, msg in master.recv_worker_msgs():
            got[mgr.name].append((msg_type, msg))
        check(got['t1']) == [(1, 'abc'), (2, None), (None, None)]
        check(got['t2']) == [(1, 'abc'), (2, None), (None, None)]
