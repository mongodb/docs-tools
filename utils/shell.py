import os
import subprocess
from tempfile import NamedTemporaryFile

try:
    from structures import AttributeDict
except ImportError:
    # support for bootstrapping
    from utils.structures import AttributeDict

class CommandError(Exception): pass

class DevNull(object):
    name = os.devnull

def command(command, capture=False, ignore=False):
    if capture is False:
        tmp_out = DevNull()
        tmp_err = DevNull()
    else:
        tmp_out = NamedTemporaryFile()
        tmp_err = NamedTemporaryFile()

    with open(tmp_out.name, 'w') as tout:
        with open(tmp_err.name, 'w') as terr:
            p = subprocess.Popen(command, stdout=tout, stderr=terr, shell=True)

            while True:
                if p.poll() is not None:
                    break

    if capture is False:
        stdout = ""
        stderr = ""
    else:
        with open(tmp_out.name, 'r') as f:
            stdout = ''.join(f.readlines()).strip()
        with open(tmp_err.name, 'r') as f:
            stderr = ''.join(f.readlines()).strip()

    out = AttributeDict({
        'cmd': command,
        'err': stderr,
        'out': stdout,
        'return_code': p.returncode,
        'succeeded': True if p.returncode == 0 else False,
        'failed': False if p.returncode == 0 else True,
        'captured': capture,
    })

    if out.succeeded is True or ignore is True:
        return out
    else:
        raise CommandError('[ERROR]: "{0}" returned {1}'.format(out.cmd, out.return_code))
