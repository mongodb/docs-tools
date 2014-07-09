import os
import subprocess
import logging
from tempfile import NamedTemporaryFile

logger = logging.getLogger('giza.command')

class CommandError(Exception): pass

class DevNull(object):
    name = os.devnull

class CommandResult(object):
    def __init__(self, cmd=None, err=None, out=None, return_code=None):
        self._cmd = cmd
        self._err = err
        self._out = out
        self._return_code = return_code
        self._captured = ''

    @property
    def succeeded(self):
        return True if self.return_code == 0 else False

    @property
    def failed(self):
        return False if self.return_code == 0 else True

    @property
    def cmd(self):
        return self._cmd

    @cmd.setter
    def cmd(self, value):
        self._cmd = value

    @property
    def err(self):
        return self._err

    @err.setter
    def err(self, value):
        self._err = value

    @property
    def out(self):
        return self._out

    @out.setter
    def out(self, value):
        self._out = value

    @property
    def return_code(self):
        return self._return_code

    @return_code.setter
    def return_code(self, value):
        if not isinstance(value, int):
            raise CommandError('invalid return code type')
        else:
            self._return_code = value

    @property
    def captured(self):
        return self._captured

    @captured.setter
    def captured(self, value):
        self._captured = value


def command(command, capture=False, ignore=False):
    logger.debug("running '{0}'".format(command))
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

    out = CommandResult(cmd=command,
                        err=stderr,
                        out=stdout,
                        return_code=p.returncode)
    out.captured = capture

    if out.succeeded is True or ignore is True:
        return out
    else:
        raise CommandError('[ERROR]: "{0}" returned {1}'.format(out.cmd, out.return_code))

def verbose_command(cmd, capture=False, ignore=False):
    logger.info("running command: " + cmd)
    command(cmd, capture, ignore)
