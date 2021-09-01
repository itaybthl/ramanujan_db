from pool_handler import WorkerPool
from multiprocessing import Manager
import config
import logging
import logging.config
import signal
import numpy as np
import os
import sys

LOGGER_NAME = 'job_logger'

MOD_PATH = 'jobs.job_%s'
POOL_SIZE = 1

def wrap_handler(worker_pool):
    def signal_handler(sig, frame):
        worker_pool.stop()
    return signal_handler

def parse_config_file():
    pool_size = config.configuration['pool_size']
    modules = {}
    for mod_name, job_config in config.configuration['jobs_to_run'].items():
        module_path = MOD_PATH % mod_name
        modules[module_path] = job_config

    return pool_size, modules

def main():
    os.makedirs(os.path.join(os.getcwd(), 'logs'), exist_ok=True)
    with open('pid.txt', 'w') as pid_file:
        pid_file.writelines([str(os.getpid()), os.linesep])
    pool_size, modules = parse_config_file()
    worker_pool = WorkerPool(pool_size)
    signal.signal(signal.SIGINT, wrap_handler(worker_pool))
    results = []
    results = worker_pool.start(modules)
    logging.config.fileConfig('logging.config', defaults={'log_filename': 'main'})

    for module_path, timings in results:
        if timings:
            logging.getLogger('job_logger').info(f'-------------------------------------')
            logging.getLogger('job_logger').info(f'module {module_path} running times:')
            logging.getLogger('job_logger').info(f'min time: {min(timings)}')
            logging.getLogger('job_logger').info(f'max time: {max(timings)}')
            logging.getLogger('job_logger').info(f'median time: {np.median(timings)}')
            logging.getLogger('job_logger').info(f'average time: {np.average(timings)}')
            logging.getLogger('job_logger').info(f'-------------------------------------')
        else:
            logging.getLogger('job_logger').info(f'-------------------------------------')
            logging.getLogger('job_logger').info(f"module {module_path} didn't run")
            logging.getLogger('job_logger').info(f'-------------------------------------')
        

def stop():
    print('stopping')
    with open('pid.txt', 'r') as pid_file:
        lines = pid_file.readlines()
    pid = lines[0].strip()
    if os.name == 'nt':
        sig = signal.CTRL_C_EVENT
    else:
        sig = signal.SIGINT
    os.kill(int(pid), sig)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Only commands are start and stop')
        exit(1)

    if sys.argv[1] == 'stop':
        stop()
    elif sys.argv[1] == 'start':
        main()
    else:
        print('Only commands are start and stop')
        exit(1)
