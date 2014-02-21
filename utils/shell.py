import os
import re
import subprocess
from tempfile import NamedTemporaryFile

try:
    from structures import AttributeDict
except ImportError:
    # support for bootstrapping
    from utils.structures import AttributeDict


def shell_value(args, path=None):
    if path is None:
        path = os.getcwd()

    if isinstance(args , str):
        r = re.compile("\s+")
        args = r.split(args)

    p = subprocess.Popen(args, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    r = p.communicate()

    return str(r[0].decode().rstrip())

class CommandError(Exception): pass

class DevNull(object):
    name = os.devnull

def command(command, capture=False, ignore=False):
    if capture is False:
        tmp_out = DevNull()
    else:
        tmp_out = NamedTemporaryFile()

    with open(tmp_out.name, 'w') as tout:
        try:
            stdout = subprocess.check_output(command, stderr=tout, shell=True)
            returncode = 0
        except subprocess.CalledProcessError as e:
            returncode = e.returncode
            stdout = e.output

    if capture is False:
        stdout = ""
        stderr = ""
    else:
        with open(tmp_out.name, 'r') as f:
            stderr = ''.join(f.readlines())

    out = {
        'cmd': command,
        'err': stderr,
        'out': stdout,
        'return_code': returncode,
        'succeeded': True if returncode == 0 else False,
        'failed': False if returncode == 0 else True
    }

    out = AttributeDict(out)

    if ignore is True:
        return out
    elif out.succeeded is True:
        if capture is True:
            return out
        else:
            return None
    else:
        raise CommandError('[ERROR]: "{0}" returned {1}'.format(out.cmd, out.return_code))
