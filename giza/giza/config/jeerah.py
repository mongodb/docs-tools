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

import os.path
import logging
import datetime

logger = logging.getLogger('giza.config.jeerah')

from libgiza.config import ConfigurationBase, RecursiveConfigurationBase
from giza.config.runtime import RuntimeStateConfigurationBase


def fetch_config(args):
    c = JeerahConfig()
    c.ingest(args.conf_path)
    c.runstate = args

    return c


class JeerahRuntimeStateConfig(RuntimeStateConfigurationBase):
    _option_registry = ['project', 'user_conf_path']

    @property
    def sprint(self):
        if 'sprint' in self.state:
            return self.state['sprint']
        else:
            return 'current'

    @sprint.setter
    def sprint(self, value):
        self.state['sprint'] = value

    @property
    def conf_path(self):
        if 'conf_path' not in self.state:
            self.conf_path = None

        return self.state['conf_path']

    @conf_path.setter
    def conf_path(self, value):
        if value is not None and os.path.exists(value):
            self.state['conf_path'] = value
        else:
            try:
                self._discover_conf_file('.scrumpy.yaml')
            except OSError:
                self._discover_conf_file('scrumpy.yaml')
            except OSError:
                logger.error('could not find scrumpy config file.')
                raise OSError


class JeerahConfig(ConfigurationBase):

    @property
    def runstate(self):
        return self.state['runstate']

    @runstate.setter
    def runstate(self, value):
        if isinstance(value, JeerahRuntimeStateConfig):
            value.conf = self
            self.state['runstate'] = value
        else:
            msg = "invalid runtime state"
            logger.critical(msg)
            raise TypeError(msg)

    @property
    def buckets(self):
        if 'buckets' in self.state:
            return self.state['buckets']
        else:
            return {}

    @buckets.setter
    def buckets(self, value):
        if isinstance(value, dict):
            if 'buckets' in self.state:
                self.state['buckets'].update(value)
            else:
                self.state['buckets'] = value
        else:
            raise TypeError('{0} is not a dict'.format(value))

    @property
    def sprints(self):
        return self.state['sprints']

    @sprints.setter
    def sprints(self, value):
        if isinstance(value, SprintCollectionConfig):
            self.state['sprints'] = value
        else:
            self.state['sprints'] = SprintCollectionConfig(value)

    @property
    def site(self):
        return self.state['site']

    @site.setter
    def site(self, value):
        if isinstance(value, JeerahSiteConfig):
            self.state['site'] = value
        else:
            self.state['site'] = JeerahSiteConfig(value)

    @property
    def reporting(self):
        return self.state['reporting']

    @reporting.setter
    def reporting(self, value):
        if isinstance(value, ReportingConfig):
            self.state['reporting'] = value
        else:
            self.state['reporting'] = ReportingConfig(value)

    @property
    def modification(self):
        return self.state['modification']

    @modification.setter
    def modification(self, value):
        if isinstance(value, ModificationConfig):
            self.state['modification'] = value
        else:
            self.state['modification'] = ModificationConfig(value, self)


class SprintCollectionConfig(ConfigurationBase):

    def ingest(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self._add_sprint(k, v)
        elif isinstance(obj, list):
            for item in obj:
                self._add_sprint(item['name'], item)
        else:
            logger.error('{0} is malformed sprint description'.format(obj))

    def _add_sprint(self, name, sprint):
        # compatibility shim:
        if isinstance(sprint, list):
            rendered_sprint = {
                'name': name,
                'fix_versions': sprint,
            }
        else:
            rendered_sprint = sprint

        # commit object to interface's storage
        try:
            self.state[name] = SprintConfig(rendered_sprint)
        except:
            logger.error('{0} is not a valid sprint'.format(name))

    def get_sprint_versions(self, name):
        if name in self.state:
            return self.state[name].fix_versions
        else:
            logger.error("sprint '{0}' does not exist".format(name))

    def get_sprint(self, name):
        if name in self.state:
            return self.state[name]
        else:
            logger.error("sprint '{0}' does not exist".format(name))


class SprintConfig(ConfigurationBase):
    _option_registry = ['fix_versions', 'name', 'staffing']

    @property
    def quota(self):
        if 'quota' in self.state:
            return self.state['quota']
        elif 'staffing' in self:
            self.quota = sum([v for v in self.staffing.values()])
            return self.state['quota']
        else:
            return None

    @quota.setter
    def quota(self, value):
        if isinstance(value, (int, float, complex)):
            self.state['quota'] = value
        else:
            raise TypeError('{0} is not a valid sprint quota')

    @property
    def start(self):
        if 'start' in self.state:
            return self.state['start']
        else:
            return None

    @start.setter
    def start(self, value):
        if isinstance(value, datetime.date):
            self.state['start'] = value
        else:
            try:
                self.state['start'] = datetime.datetime.strptime(value, "%Y-%m-%d")
            except:
                logger.warning('{0} is not a properly formed date. (use YYYY-MM-DD)'.format(value))

    @property
    def end(self):
        if 'end' in self.state:
            return self.state['end']
        else:
            return None

    @end.setter
    def end(self, value):
        if isinstance(value, datetime.date):
            self.state['end'] = value
        else:
            try:
                self.state['end'] = datetime.datetime.strptime(value, "%Y-%m-%d")
            except:
                logger.warning('{0} is not a properly formed date. (use YYYY-MM-DD)'.format(value))


class JeerahSiteConfig(ConfigurationBase):
    _option_registry = ['url']

    @property
    def credentials(self):
        return self.state['credentials']

    @credentials.setter
    def credentials(self, value):
        value = os.path.expanduser(value)
        self.state['credentials'] = value

    @property
    def projects(self):
        return self.state['project']

    @projects.setter
    def projects(self, value):
        if isinstance(value, list):
            self.state['project'] = value
        else:
            self.state['project'] = [value]


class ReportingConfig(ConfigurationBase):

    @property
    def units(self):
        if 'units' not in self.state:
            return 'hours'
        else:
            return self.state['units']

    @units.setter
    def units(self, value):
        possible_values = ('days', 'hours', 'count')
        if value in possible_values:
            self.state['units'] = value
        else:
            raise TypeError('{0} is not in {1}'.format(value, possible_values))

    @property
    def format(self):
        if 'format' not in self.state:
            return 'json'
        else:
            return self.state['format']

    @format.setter
    def format(self, value):
        if value in ('json', 'yaml'):
            self.state['format'] = value


class ModificationConfig(RecursiveConfigurationBase):

    @property
    def mirroring(self):
        return self.state['mirroring']

    @mirroring.setter
    def mirroring(self, value):
        if isinstance(value, ProjectMirroringConfig):
            self.state['mirroring'] = value
        else:
            self.state['mirroring'] = ProjectMirroringConfig(value, self.conf)


class ProjectMirroringConfig(RecursiveConfigurationBase):

    @property
    def source(self):
        # can't validate this during injestion/setting because self.conf may not
        # point to a populated config object yet.

        value = self.state['source']

        if value not in self.conf.site.projects:
            logger.warning('{0} is not a valid project'.format(value))

        return value

    @source.setter
    def source(self, value):
        self.state['source'] = value

    @property
    def target(self):
        # can't validate this during injestion/setting because self.conf may not
        # point to a populated config object yet.

        value = self.state['target']

        for project in value:
            if project not in self.conf.site.projects:
                m = '{0} is not in the list of projects ({1})'
                logger.warning(m.format(project, self.conf.site.projects))

        return value

    @target.setter
    def target(self, value):
        if isinstance(value, list):
            self.state['target'] = value
        else:
            self.state['target'] = [value]
