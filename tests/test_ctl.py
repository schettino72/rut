import io
from contextlib import redirect_stdout
from pathlib import Path

import msgpack
from rut import check

from rut.saq import Message, MessageType
from rut.collect import Collector
from rut import ctl


SAMPLE_PROJ_ROOT = Path(__file__).parent / 'sample_proj'


class TestSingleWorker:
    def test_run_all(self):
        col = Collector()
        pkg_path = str(SAMPLE_PROJ_ROOT / 'proj_inplace')
        col.process_args([pkg_path])

        rut_out = io.StringIO()
        with redirect_stdout(rut_out):
            ctl.single_worker(col, exitfirst=False)
        check(rut_out.getvalue()).has_line('proj_inplace.test_bar::test_bar: ERROR')
        check(rut_out.getvalue()).has_line('proj_inplace.test_foo::TestClass.test_abc: OK')

    def test_exit_first(self):
        col = Collector()
        pkg_path = str(SAMPLE_PROJ_ROOT / 'proj_inplace')
        col.process_args([pkg_path])

        rut_out = io.StringIO()
        with redirect_stdout(rut_out):
            ctl.single_worker(col, exitfirst=True)
        out_lines = rut_out.getvalue().splitlines()
        assert 'proj_inplace.test_bar::test_bar: ERROR' in out_lines
        assert 'proj_inplace.test_foo::TestClass.test_abc: OK' not in out_lines


class TestSubWorker:
    def test_work(self):
        payload = msgpack.packb('proj_inplace.test_foo')
        header = Message.make_header(MessageType.JOB, len(payload))
        worker_in = io.BytesIO(header + payload)
        worker_out = io.BytesIO()
        imp_spec = f'proj_inplace|{SAMPLE_PROJ_ROOT}/proj_inplace/__init__.py'
        ctl.mp_worker(imp_spec, worker_in, worker_out)
        worker_out.seek(0)
        got = []
        while header := worker_out.read(5):
            _type, _size = Message.read_header(header)
            if _type == MessageType.DATA:
                payload = msgpack.unpackb(worker_out.read(_size)) if _size else None
                got.append(payload)
        check(got[0]['c']) == 'test_ok'
        check(got[0]['r']) == 'SUCCESS'
        check(got[1]['c']) == 'TestClass.test_xxx'
        check(got[2]['c']) == 'TestClass.test_abc'
        check(len(got)) == 3


class TestMaster:
    async def test_run_all(self):
        col = Collector()
        pkg_path = str(SAMPLE_PROJ_ROOT / 'proj_inplace')
        col.process_args([pkg_path])

        rut_out = io.StringIO()
        with redirect_stdout(rut_out):
            await ctl.mp_master(col, np=1)
        check(rut_out.getvalue()).has_line('proj_inplace.test_bar::test_bar: ERROR')
        check(rut_out.getvalue()).has_line('proj_inplace.test_foo::TestClass.test_abc: OK')
