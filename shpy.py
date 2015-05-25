import logging
import subprocess
import sys
import select
import shlex
from cStringIO import StringIO

logging.basicConfig(format="%(asctime)s %(out)3s %(prog)8s %(message)s", level=logging.DEBUG)


def c(str, *args):
    p = subprocess.Popen(shlex.split(str.format(*args)),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds=True)

    stdout = StringIO()
    stderr = StringIO()

    while True:
        reads = [p.stdout.fileno(), p.stderr.fileno()]
        ret = select.select(reads, [], [])

        for fd in ret[0]:
            if fd == p.stdout.fileno():
                read = p.stdout.readline()
                stdout.write(read)
                logging.info(read.rstrip(), extra={'prog':str, 'out':'out'})

            if fd == p.stderr.fileno():
                read = p.stderr.readline()
                stderr.write(read)
                logging.info(read.rstrip(), extra={'prog':str, 'out':'err'})

        if p.poll() != None:
            break

    print 'program ended ', p.returncode
    print 'stdout:\n', stdout.getvalue()
    print 'stderr:\n', stderr.getvalue()

