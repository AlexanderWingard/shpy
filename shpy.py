import sys
import argparse
import logging
import subprocess
import signal
import shlex
import re
from subprocess import Popen, PIPE
from threading import Thread
from Queue import Queue, Empty

parser = argparse.ArgumentParser()
parser.add_argument('--verbose', '-v', action='count')

def init():
    args = parser.parse_args()
    if args.verbose == 0 or args.verbose is None:
        logging.basicConfig(format="%(message)s",
                            level=logging.ERROR)
    elif args.verbose == 1:
        logging.basicConfig(format="%(message)s",
                            level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(format="%(message)s",
                            level=logging.INFO)
    elif args.verbose > 2:
        logging.basicConfig(format="%(asctime)s %(out)6s | %(message)s",
                            level=logging.DEBUG)
    return args

children = []

def c(str, *args, **kwargs):
    jobs = Queue()
    def line_reader(pipe, result, label, logfun):
        jobs.get()
        for line in iter(pipe.readline, b''):
            line = line.rstrip()
            logfun(line, extra={'out':label})
            result.append(line)
        jobs.task_done()

    def pipe_watch(pipe, label, logfun):
        jobs.put(1)
        result = []
        t = Thread(target=line_reader, args=[pipe, result, label, logfun])
        t.daemon = True
        t.start()
        return result


    cl = str.format(*args)
    logging.debug(cl, extra={'out':'CALL'})
    p = subprocess.Popen(shlex.split(cl),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds=True,
                         cwd=kwargs.get('cwd'))

    children.append(p)
    outres = pipe_watch(p.stdout, "OUT", logging.info)
    errres = pipe_watch(p.stderr, "ERROR", logging.warning)
    rescode = p.wait()
    children.remove(p)
    jobs.join()
    logging.debug(rescode, extra={'out':'RETURN'})
    if not rescode == 0 and kwargs.get('exit') is None:
        if logging.getLogger().getEffectiveLevel() >= logging.WARNING:
            for line in outres:
                logging.error("%s", line, extra={'out':'FAULTO'})
            for line in errres:
                logging.error("%s", line, extra={'out':'FAULTE'})
        logging.error("%s exited with code: %d", cl, rescode, extra={'out':'FAULT'})
        sys.exit(rescode)
    return outres


def kill_children(signum, frame):
    for p in children:
        try:
            p.terminate();
            logging.debug("Killing {}".format(p.pid), extra={'out':'KILL'});
        except:
            pass
    sys.exit(signum)

signal.signal(signal.SIGINT, kill_children)

def exists(regex, lines):
    reg = re.compile(regex)
    for line in lines:
        if reg.match(line):
            return True
    return False
