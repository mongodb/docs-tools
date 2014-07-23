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

import logging
import os.path

logger = logging.getLogger('giza.config.paths')

from giza.strings import hyph_concat
from giza.config.base import RecursiveConfigurationBase

class PathsConfig(RecursiveConfigurationBase):
    @property
    def output(self):
        return self.state['output']

    @output.setter
    def output(self, value):
        self.state['output'] = value

    @property
    def source(self):
        return self.state['source']

    @source.setter
    def source(self, value):
        self.state['source'] = value

    @property
    def includes(self):
        return self.state['includes']

    @includes.setter
    def includes(self, value):
        self.state['includes'] = value

    @property
    def images(self):
        return self.state['images']

    @images.setter
    def images(self, value):
        self.state['images'] = value

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = value

    @property
    def buildsystem(self):
        return self.state['buildsystem']

    @buildsystem.setter
    def buildsystem(self, value):
        self.state['buildsystem'] = value

    @property
    def builddata(self):
        return self.state['builddata']

    @builddata.setter
    def builddata(self, value):
        self.state['builddata'] = value

    @property
    def locale(self):
        if self.conf.project.edition is not None and self.conf.project.edition != self.conf.project.name:
            return hyph_concat(self.state['locale'], self.conf.project.edition)
        else:
            return self.state['locale']

    @locale.setter
    def locale(self, value):
        self.state['locale'] = value

    @property
    def buildarchive(self):
        if 'buildarchive' not in self.state:
            self.buildarchive = None
        return os.path.join(self.output, 'archive')

    @buildarchive.setter
    def buildarchive(self, value):
        self.state['buildarchive'] = os.path.join(self.output, 'archive')

    @property
    def global_config(self):
        return os.path.join(self.buildsystem, 'data')

    @global_config.setter
    def global_config(self, value):
        logger.error('global_config is dynamically rendered')

    @property
    def projectroot(self):
        p = os.getcwd()
        self.state['projectroot'] = os.getcwd()
        return p

    @property
    def public(self):
        if 'public' not in self.state:
            self.public = None

        return self.state['public']

    @public.setter
    def public(self, value):
        if self.conf.runstate.language in (None, 'en'):
            public_path = 'public'
        else:
            public_path = '-'.join(('public', self.conf.runstate.language))

        self.state['public'] = os.path.join(self.output, public_path)

    @property
    def branch_output(self):
        if 'branch_output' not in self.state:
            self.branch_output = None

        return self.state['branch_output']

    @branch_output.setter
    def branch_output(self, value):
        self.state['branch_output'] = os.path.join(self.output, self.conf.git.branches.current)

    @property
    def branch_source(self):
        if 'branch_source' not in self.state:
            self.branch_source = None

        return self.state['branch_source']

    @branch_source.setter
    def branch_source(self, value):
        p = os.path.join(self.branch_output, self.source)
        if (self.conf.project.edition is not None and
            self.conf.project.edition != self.conf.project.name):
            p += '-' + self.conf.project.edition

        self.state['branch_source'] = p

    @property
    def branch_staging(self):
        if 'branch_staging' not in self.state:
            self.branch_staging = None

        return self.state['branch_staging']

    @branch_staging.setter
    def branch_staging(self, value):
        self.state['branch_staging'] = os.path.join(self.public, self.conf.git.branches.current)

    @property
    def global_config(self):
        if 'global_config' not in self.state:
            self.global_config = None

        return self.state['global_config']

    @global_config.setter
    def global_config(self, value):
        self.state['global_config'] = os.path.join(self.buildsystem, 'data')

    @property
    def public_site_output(self):
        if 'public_site_output' not in self.state:
            self.public_site_output = None

        return self.state['public_site_output']

    @public_site_output.setter
    def public_site_output(self, value):
        p = [ self.conf.paths.public ]

        if (self.conf.project.edition != self.conf.project.name and
            self.conf.project.edition is not None):
            p.append(self.conf.project.edition)

        if self.conf.project.branched is True:
            p.append(self.conf.git.branches.current)

        p = os.path.sep.join(p)

        if (self.conf.project.branched is False and
            self.conf.project.edition is not None and
            self.conf.git.branches.current != self.conf.git.branches.published[0]):
            p += '-' + self.conf.git.branches.current

        self.state['public_site_output'] = p
