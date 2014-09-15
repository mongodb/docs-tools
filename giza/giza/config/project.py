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

from giza.config.base import RecursiveConfigurationBase, ConfigurationBase

def get_path_prefix(conf, branch):
    """
    Returns the part of a site path between the domain name and the paths
    produced from sprint, accounting for sub-site names and branch names.
    """

    o = []

    if conf.project.siteroot is True:
        if (conf.project.branched is True and
            conf.git.branches.manual != branch):
            o.append(branch)
        else:
            o.append(conf.project.tag)
    else:
        o.append(conf.project.basepath)

        if conf.project.branched is True:
            if conf.git.branches.manual == conf.git.branches.current:
                o.append('current')
            else:
                o.append(branch)

    return '/'.join(o)

def get_current_path(conf):
    branch = conf.git.branches.current
    if branch not in conf.git.branches.published:
        branch = conf.git.branches.published[0]

    return get_path_prefix(conf, branch)

class ProjectConfig(RecursiveConfigurationBase):
    _option_registry = ['name', 'tag', 'url', 'title']

    @property
    def editions(self):
        if 'editions' in self.state:
            return self.state['editions']
        else:
            return []

    @property
    def edition_list(self):
        if '_edition_list' in self.state: 
            return self.state['_edition_list']
        else: 
            return []

    @editions.setter
    def editions(self, value):
        if isinstance(value, list):
            if '_edition_list' not in self.state:
                self.state['_edition_list'] = []
            if 'editions' not in self.state:
                self.state['editions'] = []

            self.state['_edition_list'].extend( [ v['name'] for v in value ] )
            self.state['editions'].extend([EditionListConfig(v) for v in value])
        else:
            logger.critical('editions must be a list')
            raise TypeError

    @property
    def edition(self):
        if 'edition' not in self.state or self.state['edition'] is None:
            self.edition = None

        return self.state['edition']

    @edition.setter
    def edition(self, value):
        if 'editions' in self.state and self.conf.runstate.edition in self.state['_edition_list']:
            self.state['edition'] = self.conf.runstate.edition
        else:
            self.state['edition'] = self.name

    @property
    def branched(self):
        if 'branched' not in self.state:
            self.branched = None

        return self.state['branched']

    @branched.setter
    def branched(self, value):
        if isinstance(value, bool):
            self.state['branched'] = value
        else:
            self.state['branched'] = False
            for edition in self.editions:
                if self.edition == edition.name:
                    self.state['branched'] = edition.branched
                    break

    @property
    def basepath(self):
        if 'basepath' not in self.state:
            self.basepath = None

        return self.state['basepath']

    @basepath.setter
    def basepath(self, value):
        if value is not None:
            self.state['basepath'] = value
        else:
            self.state['basepath'] = self.tag

            for edition in self.editions:
                if self.edition == edition.name:
                    self.state['basepath'] = edition.tag
                    break

    @property
    def siteroot(self):
        if 'siteroot' in self.state:
            return self.state['siteroot']
        else:
            return False

    @siteroot.setter
    def siteroot(self, value):
        if isinstance(value, bool):
            self.state['siteroot'] = value
        else:
            self.state['siteroot'] = bool(value)

    @property
    def sitepath(self):
        return get_path_prefix(self.conf, self.conf.git.branches.current)

class EditionListConfig(ConfigurationBase):
    _option_registry = ['name']

    @property
    def branched(self):
        if 'branched' in self.state:
            return self.state['branched']
        else:
            return False

    @branched.setter
    def branched(self, value):
        if isinstance(value, bool):
            self.state['branched'] = value
        else:
            raise TypeError

    @property
    def tag(self):
        if 'tag' not in self.state:
            return None
        else:
            return self.state['tag']

    @tag.setter
    def tag(self, value):
        self.state['tag'] = value
