import sys
import logging

from .saq import Master, Worker, MessageType
from .case import CaseOutcome
from .collect import Collector, Selector
from .runner import Runner
from .reporter import Reporter


log = logging.getLogger(__name__)


def single_worker(collector, exitfirst):
    """run all test cases in a single process"""
    selector = Selector(collector.mods)
    reporter = Reporter()
    runner = Runner()
    for outcome in runner.execute(selector):
        reporter.handle_outcome(outcome)
        if exitfirst and outcome.result in ('ERROR', 'FAIL'):
            break
    return 0


async def mp_master(collector, np):
    """master process when using multiple processes"""
    manager = Master()

    # a testing module is the minimum unit sent as a job to workers
    mods = collector.mods[:]
    imp_spec = '|'.join(collector.specs[0])
    for wid in range(np):
        mod = mods.pop(0)
        if mod:
            work_mgr = await manager.exec(f't{wid}', f'rut --worker --imp {imp_spec}')
            log.info('MASTER send job %s', mod)
            work_mgr.send_job(mod)

    reporter = Reporter()
    async for work_mgr, msg_type, msg in manager.recv_worker_msgs():
        log.info('MASTER got %s', msg_type)
        if msg_type == MessageType.READY:
            if mods:
                mod = mods.pop(0)
                log.info('MASTER send job %s', mod)
                work_mgr.send_job(mod)
            else:
                # closing stdin signals the process to terminate
                log.info('MASTER closing stdin')
                work_mgr.process.stdin.close()
            continue

        if msg_type == MessageType.DATA:
            outcome = CaseOutcome.from_data(msg)
            reporter.handle_outcome(outcome)
            continue

        assert msg_type == MessageType.DONE
        # print(f'[{work_mgr.name}] DONE')

        # print captured/piped stderr from subprocess - currently not being piped
        if work_mgr.process.stderr:  # pragma: no cover
            err = await work_mgr.process.stderr.read()
            if err:
                print(f'====== {work_mgr.name}:',
                      f'Error ({work_mgr.process.returncode}) =====')
                print(err.decode().rstrip())
                print('===================================')
                print(f'[{work_mgr.name}] ERROR')
    # print('all done')
    return 0



# echo -ne '\x01\x00\x00\x00\x13\xb2tests.test_collect\x01\x00\x00\x00\x12\xb1tests.test_runner' # noqa
#          | rut --worker --imp 'tests|tests/__init__.py'
def mp_worker(imp_spec):
    """worker process when using multiple processes"""
    worker = Worker(sys.stdin.buffer, sys.stdout.buffer)
    imp_name, imp_path = imp_spec.split('|')
    Collector.import_spec(imp_name, imp_path)
    runner = Runner()
    for msg in worker.recv_data():
        selector = Selector([msg])
        for outcome in runner.execute(selector):
            worker.send_msg(outcome.pack())
    return 0
