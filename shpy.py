import logging
import subprocess
import sys
import select
import shlex
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK
from cStringIO import StringIO

logging.basicConfig(format="%(asctime)s %(out)3s %(prog)8s %(message)s", level=logging.DEBUG)


def c(str, *args):
    p = subprocess.Popen(shlex.split(str.format(*args)),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds=True)

    flags = fcntl(p.stdout, F_GETFL)
    fcntl(p.stdout, F_SETFL, flags | O_NONBLOCK)
    flags = fcntl(p.stderr, F_GETFL)
    fcntl(p.stderr, F_SETFL, flags | O_NONBLOCK)


    stdout = StringIO()
    stderr = StringIO()

    while True:
        reads = [p.stdout.fileno(), p.stderr.fileno()]
        ret = select.select(reads, [], [])

        for fd in ret[0]:
            if fd == p.stdout.fileno():
                try:
                    for read in iter(p.stdout.readline, b''):
                        stdout.write(read)
                        logging.info(read.rstrip(), extra={'prog':str, 'out':'out'})
                except:
                    pass

            if fd == p.stderr.fileno():
                try:
                    for read in iter(p.stderr.readline, b''):
                        stderr.write(read)
                        logging.info(read.rstrip(), extra={'prog':str, 'out':'err'})
                except:
                    pass

        if p.poll() != None:
            break

    print 'program ended ', p.returncode
    print 'stdout:\n', stdout.getvalue()
    print 'stderr:\n', stderr.getvalue()

