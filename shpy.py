import logging
import subprocess
import shlex
from subprocess import Popen, PIPE
from threading import Thread
from Queue import Queue, Empty

#logging.basicConfig(format="%(asctime)s %(out)6s %(prog)8s | %(message)s", level=logging.DEBUG)
logging.basicConfig(format="%(asctime)s %(out)6s | %(message)s", level=logging.DEBUG)

def c(str, *args, **kwargs):
    jobs = Queue()
    def line_reader(pipe, result, label):
        jobs.get()
        for line in iter(pipe.readline, b''):
            line = line.rstrip()
            logging.info(line, extra={'prog':str, 'out':label})
            result.append(line)
        jobs.task_done()

    def pipe_watch(pipe, label):
        jobs.put(1)
        result = []
        t = Thread(target=line_reader, args=[pipe, result, label])
        t.daemon = True
        t.start()
        return result


    cl = str.format(*args)
    logging.info(cl, extra={'prog':'', 'out':'CALL'})
    p = subprocess.Popen(shlex.split(cl),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds=True)

    outres = pipe_watch(p.stdout, "OUT")
    errres = pipe_watch(p.stderr, "ERROR")
    rescode = p.wait()
    jobs.join()
    logging.info(rescode, extra={'prog':'', 'out':'RETURN'})
    #if not rescode == 0:
    #    raise subprocess.CalledProcessError(rescode, cmd=cl, output="\n".join(errres))
    return outres
