import sys
import logging

from .saq import Master, Worker, MessageType
from .case import CaseOutcome
from .collect import Collector, Selector
from .runner import Runner
from .reporter import Reporter


log = logging.getLogger(__name__)


def single_worker(collector, *, capture='sys', exitfirst=False):
    """run all test cases in a single process"""
    selector = Selector(collector.mods)
    reporter = Reporter()
    runner = Runner(capture)
    for outcome in runner.execute(selector):
        reporter.handle_outcome(outcome)
        if exitfirst and outcome.result in ('ERROR', 'FAIL'):
            break
    return 0


# echo -ne '\x01\x00\x00\x00\x13\xb2tests.test_collect\x01\x00\x00\x00\x12\xb1tests.test_runner' # noqa
#          | rut --worker --imp 'tests|tests/__init__.py'
def mp_worker(imp_spec, in_stream=None, out_stream=None):
    """worker process when using multiple processes"""
    worker_in = in_stream if in_stream else sys.stdin.buffer
    worker_out = out_stream if out_stream else sys.stdout.buffer
    worker = Worker(worker_in, worker_out)
    imp_name, imp_path = imp_spec.split('|')
    Collector.import_spec(imp_name, imp_path)
    runner = Runner()
    for msg in worker.recv_data():
        selector = Selector([msg])
        for outcome in runner.execute(selector):
            worker.send_msg(outcome.pack())
    return 0


async def mp_master(collector, np):
    """master process when using multiple processes"""
    master = Master()

    # a testing module is the minimum unit sent as a job to workers
    mods = list(reversed(collector.mods))
    assert len(collector.specs) == 1
    imp_spec = '|'.join(collector.specs[0])
    for wid in range(np):
        mod = mods.pop()
        if mod:
            cmd = f'rut --worker --imp {imp_spec}'
            work_mgr = await master.add_worker(f't{wid}', cmd)
            log.info('MASTER send job %s', mod)
            work_mgr.send_job(mod)

    reporter = Reporter()
    async for work_mgr, msg_type, msg in master.recv_worker_msgs():
        log.info('MASTER got %s', msg_type)

        # worker is READY: send another job
        if msg_type == MessageType.READY:
            if mods:
                mod = mods.pop()
                log.info('MASTER send job %s', mod)
                work_mgr.send_job(mod)
            else:
                # closing stdin signals the process to terminate
                log.info('MASTER closing stdin to {work_mgr.name}')
                work_mgr.process.stdin.close()
            continue

        # got some data/output from worker
        if msg_type == MessageType.DATA:
            outcome = CaseOutcome.from_data(msg)
            reporter.handle_outcome(outcome)
            continue

        # worker is DONE: do any cleanup necessary
        assert msg_type == MessageType.DONE
        # print captured/piped stderr from subprocess - currently not being piped
        if work_mgr.process.stderr:  # pragma: no cover
            err = await work_mgr.process.stderr.read()
            if err:
                print(f'====== {work_mgr.name}:',
                      f'Error ({work_mgr.process.returncode}) =====')
                print(err.decode().rstrip())
                print('===================================')
                print(f'[{work_mgr.name}] ERROR')
    return 0
