# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Given a deploy target, we need to compile the rsync commands to:

- rsync the specified source directory to the specified target directory
- rsync all static files. (unless non-master and .htaccess)
- create the rsync command.

"""

import logging
import os.path

from giza.files import InvalidFile
from giza.command import command

logger = logging.getLogger('giza.deploy')

class Deploy(object):
    def __init__(self, conf):
        self.conf = conf
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
            self.name = pspec['target']
        elif 'name' in pspec:
            self.name = pspec['name']

        self.remote_path = pspec['paths']['remote']
        self.local_path = pspec['paths']['local']

        if 'delete' in pspec['options']:
            self.delete = True

        if 'recursive' in pspec['options']:
            self.recursive = True

        self.env = pspec['env']
        self.deploy_env = getattr(self.conf.deploy, self.env)

        self.hosts = self.deploy_env.hosts

        if 'static' in pspec['paths']:
            self.static_files.extend(pspec['paths']['static'])

    def _base_cmd(self):
        base_cmd = [ 'rsync', '-cqltz']

        if self.delete is True:
            base_cmd.append('--delete')

        if self.recursive is True:
            base_cmd.append('--recursive')

        if 'args' in self.deploy_env:
            base_cmd.extend(self.deploy_env.args)

        return base_cmd

    def deploy_commands(self):
        base = self._base_cmd()

        for host in self.hosts:
            yield base + [ os.path.join(self.conf.paths.output, self.local_path) + '/',
                           host + ':' + self.remote_path ]

            for fn in self.static_files:
                if self.conf.git.branches.current != 'master' and fn == '.htaccess':
                    logger.debug('skipping .htaccess files from non-master branch')
                    continue
                else:
                    yield base + [ os.path.join(self.conf.paths.output,  self.local_path,  fn),
                                   host + ':' + self.remote_path ]

    def run(self):
        map(command, self.deploy_commands())
