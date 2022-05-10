import logging
import sys
import asyncio

import click
from rich.logging import RichHandler
import msgpack  # type: ignore

from .saq import ProcessManager
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
            worker = await manager.exec(f't{wid}', f'rut --worker --imp {imp_spec}')
            worker.write_to_worker(mod)

    reporter = Reporter()
    async for worker, msg in manager.iter_out_msgs():
        if msg:
            if msg == 'NEXT':
                if mods:
                    worker.write_to_worker(mods.pop(0))
                else:
                    # closing stdin signals the process to terminate
                    worker.process.stdin.close()
            else:
                outcome = CaseOutcome.from_data(msg)
                reporter.handle_outcome(outcome)
                # print(f'[{worker.name}] {msg}')
        else:  # completed
            err = await worker.process.stderr.read()
            if err:
                print(f'====== {worker.name}: Error ({worker.process.returncode}) =====')
                print(err.decode().rstrip())
                print('===================================')
                print(f'[{worker.name}] ERROR')
                # await worker.process.wait()
    return 0



# echo -ne '\xb2tests.test_collect\xb1tests.test_runner' | rut --worker --imp 'tests|tests/__init__.py' # noqa
def rut_worker(imp_spec):
    """worker process when using multiple processes"""
    def write(data, pack=True):
        msg = msgpack.packb(data) if pack else data
        sys.stdout.buffer.write(msg)
        sys.stdout.flush()

    imp_name, imp_path = imp_spec.split('|')
    Collector.import_spec(imp_name, imp_path)
    runner = Runner()

    unpacker = msgpack.Unpacker()
    while True:
        bin_data = sys.stdin.buffer.read(1)
        if not bin_data:
            break  # no more jobs
        unpacker.feed(bin_data)
        try:
            msg = unpacker.unpack()
        except msgpack.OutOfData:
            continue  # read more data
        if not msg:
            break
        ###################################### Actual worker logic
        # supports receiveing only module names as msg
        selector = Selector([msg])
        for outcome in runner.execute(selector):
            write(outcome.pack(), False)
        ######################################
        write('NEXT')
    return 0



if __name__ == '__main__':
    main()
