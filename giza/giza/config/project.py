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
import libgiza.config

logger = logging.getLogger('giza.config.')


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
        if conf.project.basepath not in ('', None):
            o.append(conf.project.basepath)

        if conf.project.branched is True:
            if (branch == conf.git.branches.current and
                    conf.git.branches.manual == conf.git.branches.current):
                o.append('current')
            else:
                o.append(branch)

    return '/'.join(o)


def get_current_path(conf):
    branch = conf.git.branches.current
    if branch not in conf.git.branches.published:
        branch = conf.git.branches.published[0]

    return get_path_prefix(conf, branch)


class ProjectConfig(libgiza.config.RecursiveConfigurationBase):
    _option_registry = ['name', 'title']

    @property
    def tag(self):
        if self.edition in self.edition_list:
            return self.edition_map[self.edition].tag
        elif 'tag' in self.state:
            return self.state['tag']
        else:
            return ''

    @tag.setter
    def tag(self, value):
        self.state['tag'] = value

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

    @property
    def edition_map(self):
        if '_edition_map' in self.state:
            return self.state['_edition_map']
        else:
            return {}

    @editions.setter
    def editions(self, value):
        if isinstance(value, list):
            if '_edition_list' not in self.state:
                self.state['_edition_list'] = []
            if 'editions' not in self.state:
                self.state['editions'] = []
            if '_edition_map' not in self.state:
                self.state['_edition_map'] = {}

            for v in value:
                ename = v['name']
                ed = EditionListConfig(v)
                self.state['_edition_list'].append(ename)
                self.state['editions'].append(ed)
                self.state['_edition_map'][ename] = ed
        else:
            logger.critical('editions must be a list')
            raise TypeError

    @property
    def edition(self):
        if 'edition' not in self.state or self.state['edition'] is None:
            self.edition = None
            if 'edition' not in self.state:
                return self.name
            else:
                return self.state['edition']
        else:
            return self.state['edition']

    @edition.setter
    def edition(self, value):
        if 'editions' in self.state:
            if value in self.state['_edition_list']:
                self.state['edition'] = value
            elif self.conf.runstate.edition in self.state['_edition_list']:
                self.state['edition'] = self.conf.runstate.edition

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
    def url(self):
        if 'url' not in self.state:
            self.url = None

        return self.state['url']

    @url.setter
    def url(self, value):
        url = None
        for edition in self.editions:
            if self.edition == edition.name:
                url = edition.url
                break

        if url is None:
            if value is None:
                self.state['url'] = ''
            else:
                self.state['url'] = value
        else:
            self.state['url'] = url

    @property
    def basepath(self):
        if 'basepath' not in self.state:
            self.basepath = None

        if 'basepath' in self.state:
            return self.state['basepath']
        else:
            return ''

    @basepath.setter
    def basepath(self, value):
        if value is not None:
            self.state['basepath'] = value
        else:
            for edition in self.editions:
                if self.edition == edition.name:
                    if edition.tag is None:
                        self.state['basepath'] = ''
                    else:
                        self.state['basepath'] = edition.tag

                    break

            if 'basepath' not in self.state and 'tag' in self.state:
                self.state['basepath'] = self.tag

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


class EditionListConfig(libgiza.config.ConfigurationBase):
    _option_registry = ['name', 'url']

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
