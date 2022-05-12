import sys

from .saq import Master, Worker, MessageType
from .case import CaseOutcome
from .collect import Collector, Selector
from .runner import Runner
from .reporter import Reporter



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
            work_mgr.send_job(mod)

    reporter = Reporter()
    async for work_mgr, msg_type, msg in manager.iter_out_msgs():
        if msg_type == MessageType.READY:
            if mods:
                work_mgr.send_job(mods.pop(0))
            else:
                # closing stdin signals the process to terminate
                # print(f'[{work_mgr.name}] CLOSING')
                work_mgr.process.stdin.close()
            continue

        if msg_type == MessageType.MSG:
            outcome = CaseOutcome.from_data(msg)
            reporter.handle_outcome(outcome)
            continue

        assert msg_type == MessageType.DONE
        # print(f'[{work_mgr.name}] DONE')
        err = await work_mgr.process.stderr.read()
        if err:
            print(f'====== {work_mgr.name}:',
                  f'Error ({work_mgr.process.returncode}) =====')
            print(err.decode().rstrip())
            print('===================================')
            print(f'[{work_mgr.name}] ERROR')
    # print('all done')
    return 0



# echo -ne '\x01\x00\x00\x00\x13\xb2tests.test_collect\x01\x00\x00\x00\x12\xb1tests.test_runner' | rut --worker --imp 'tests|tests/__init__.py' # noqa
def mp_worker(imp_spec):
    """worker process when using multiple processes"""
    worker = Worker(sys.stdout.buffer)
    imp_name, imp_path = imp_spec.split('|')
    Collector.import_spec(imp_name, imp_path)
    runner = Runner()

    while True:
        msg_type, msg = worker.read_one(sys.stdin.buffer)
        if msg_type is None:
            break
        assert msg_type == MessageType.JOB
        ###################################### Actual worker logic
        # supports receiveing only module names as msg
        selector = Selector([msg])
        for outcome in runner.execute(selector):
            worker.send_msg(outcome.pack())
        ######################################
        worker.send_ctl(MessageType.READY)
    worker.send_ctl(MessageType.DONE)
    return 0
