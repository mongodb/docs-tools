import sys
import subprocess
from contextlib import closing, contextmanager

def log_command_output(cmd, path, logfile, wait=False):
    with open(logfile, 'a') as f:
        p = subprocess.Popen(cmd, cwd=path, stdout=f, stderr=f)
        if wait is True:
            p.wait()

@contextmanager
def swap_streams(out):
    tmp0 = sys.stdout
    tmp1 = sys.stderr

    sys.stdout = out
    sys.stderr = out

    try:
        yield out
    finally:
        sys.stdout = tmp0
        sys.stdout = tmp1
        out.close()

def build_platform_notification(title, content):
    if sys.platform.startswith('darwin'):
        return 'growlnotify -n "mongodb-doc-build" -a "Terminal.app" -m %s -t %s' % (title, content)
    if sys.platform.startswith('linux'):
        return 'notify-send "%s" "%s"' % (title, content)
