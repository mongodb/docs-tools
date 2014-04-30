"""
Given a deploy target, we need to compile the rsync commands to:

- rsync the specified source directory to the specified target directory
- rsync all static files. (unless non-master and .htaccess)
- create the rsync command.

"""

import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from config import lazy_conf
from structures import AttributeDict

class Deploy(object):
    def __init__(self, conf=None):
        self.conf = lazy_conf(conf)
        self.name = None
        self.remote_path = None
        self.local_path = None
        self.delete = False
        self.recursive = True
        self.env = None
        self.hosts = None
        self.static_files = []

    def load(self, pspec):
        if 'target' in pspec:
            self.name = pspec.target
        elif 'name' in pspec:
            self.name = pspec.name

        self.remote_path = pspec.paths.remote
        self.local_path = pspec.paths.local

        if 'delete' in pspec.options:
            self.delete = True

        if 'recursive' in pspec.options:
            self.recursive = True

        self.env = pspec.env

        self.hosts = self.conf.deploy[self.env].hosts

        if 'static' in pspec.paths:
            self.static_files.extend(pspec.paths.static)

    def _base_cmd(self):
        base_cmd = [ 'rsync', '-cqltz']

        if self.delete is True:
            base_cmd.append('--delete')

        if self.recursive is True:
            base_cmd.append('--recursive')

        if 'args' in self.conf.deploy[self.env]:
            base_cmd.extend(self.conf.deploy[self.env].args)

        return base_cmd

    def deploy_commands(self):
        base = self._base_cmd()

        for host in self.hosts:
            yield base + [ os.path.join(self.conf.paths.public_site_output) + '/',
                           host + ':' + self.remote_path ]

            for fn in self.static_files:
                if self.conf.git.branches.current != 'master' and fn == '.htaccess':
                    logger.debug('skipping .htaccess files from non-master branch')
                    continue
                else:
                    yield base + [ os.path.join(self.conf.paths.public_site_output, fn),
                                   host + ':' + self.remote_path ]

    def run(self, p=None):
        if p is None:
            map(printer, self.deploy_commands())
        else:
            logger.critical('not running commands during test.')
            return True
            res = p.map_async(command, self.deploy_commands())
            logger.info('deployed {0} targets'.format(len(res)))



def printer(line):
    print(' '.join(line))

if __name__ == '__main__':
    d = {"target": "stage",
         "paths": {
             'remote': '/srv/public/test/ecosystem',
             'local': 'public/',
             'static': ['a', 'b', 'c', '.htaccess'] },
        'options': ['recursive'],
        'env': 'production',
        'dependency': 'stage-if-up-to-date' }

    dep = Deploy()
    dep.load(AttributeDict(d))
    dep.run()
