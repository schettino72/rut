import logging
import sys
import asyncio

import click
from rich.logging import RichHandler

from .saq import ProcessManager, Worker, MessageType
from .case import CaseOutcome
from .collect import Collector, Selector
from .runner import Runner, Reporter


log = logging.getLogger('rut')

@click.command()
# logging
# @click.option('--log-level', help='logging level', )
# @click.option('--log-file', )
@click.option('--log-show', default=False, is_flag=True,
              help='show logs on stdout/terminal')
# reporting
# runner
@click.option('-x', '--exitfirst', default=False, is_flag=True,
              help='exit instantly on first error or failed test.')
# worker
@click.option('-n', 'num_proc', default=0,
              help='number of child worker processes')
@click.option('--worker', 'is_worker', default=False, is_flag=True,
              help='run tests as worker, output as msgpack')
@click.option('--imp', help='import spec <pkg>|<path> i.e. "tests|tests/__init__.py"')
# collection / selection
@click.argument('args', nargs=-1, metavar='TESTS')
def main(args, log_show, exitfirst,
         num_proc, is_worker, imp):
    """run unittest tests

    args: python pkg/module paths
    """
    # logging.basicConfig(filename='rut.log', filemode='w', level=logging.INFO)
    if log_show:
        logging.basicConfig(
            level=logging.INFO,
            format="[cyan]%(name)s[/cyan] %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(markup=True)])

    if is_worker:
        return rut_worker(imp)

    collector = Collector()
    collector.process_args(args)
    if num_proc:
        return asyncio.run(rut_master(collector, num_proc))
    return single_worker(collector, exitfirst)


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


async def rut_master(collector, np):
    """master process when using multiple processes"""
    manager = ProcessManager()

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
def rut_worker(imp_spec):
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



if __name__ == '__main__':
    main()
