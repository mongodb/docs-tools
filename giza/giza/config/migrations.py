# Copyright 2015 MongoDB, Inc.
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
import os
import sys
import re
import giza.libgiza.config
import giza.content.helper

logger = logging.getLogger('giza.config.migrations')

if sys.version_info >= (3, 0):
    basestring = str


class MigrationData(list):
    def append(self, item):
        self.insert(-1, item)

    def extend(self, items):
        for item in items:
            self.insert(-1, item)

    def insert(self, index, item):
        if item is None:
            return
        elif giza.content.helper.edition_check(item, self.conf) is False:
            return

        if 'sources' in item:
            spec = {}
            if 'source_dir' in item:
                spec['source_dir'] = item['source_dir']
            for source in item['sources']:
                spec['source'] = source
                m = MigrationSpecification(spec, self.conf)
                super(MigrationData, self).insert(-1, m)
        else:
            m = MigrationSpecification(item, self.conf)
            super(MigrationData, self).insert(index, m)


class MigrationSpecification(giza.libgiza.config.RecursiveConfigurationBase):
    @property
    def source_dir(self):
        if 'source_dir' not in self.state:
            self.source_dir = None

        return self.state['source_dir']

    @source_dir.setter
    def source_dir(self, value):
        paths = []
        if value is not None:
            if value.startswith('/'):
                value = value[1:]
            paths.extend([
                value,
                os.path.join(self.conf.paths.projectroot, value),
                os.path.join(self.conf.paths.projectroot, self.conf.paths.output, value)])

        paths.extend([self.conf.paths.projectroot,
                      os.path.abspath(os.path.join(self.conf.paths.projectroot, '..')),
                      os.path.abspath(os.path.join(self.conf.paths.projectroot, '..', 'source')),
                      os.path.join(self.conf.paths.projectroot, self.conf.paths.source),
                      os.path.join(self.conf.paths.projectroot, self.conf.paths.output)])
        self.state['source_dir'] = paths

    @property
    def source(self):
        return self.state['source']

    @source.setter
    def source(self, value):
        if value.startswith('/'):
            value = value[1:]

        self.state['_raw_source'] = value

        fns = [os.path.join(path, value)
               for path in self.source_dir]

        for fn in fns:
            if os.path.isfile(fn):
                self.state['source'] = fn
                break

        if 'source' not in self.state:
            raise TypeError('{0} does not exist'.format(value))

    @property
    def target(self):
        if 'target' not in self.state:
            self.target = 'auto'

        return self.state['target']

    @target.setter
    def target(self, value):
        if value == 'auto':
            self.state['target'] = os.path.join(self.conf.paths.projectroot, self.conf.paths.source,
                                                self.state['_raw_source'])
            return
        elif value.startswith('/'):
            value = value[1:]

        if '{root}' in value:
            value = value.format(root=self.conf.paths.projectroot)

        if '{branch}' in value:
            value = value.format(branch=self.conf.git.brancehs.current)

        self.state['target'] = os.path.join(self.conf.paths.projectroot,
                                            self.conf.paths.source, value)

        self.state['_raw_target'] = value

    @property
    def transform(self):
        if 'transform' in self.state:
            return self.state['transform']
        else:
            return None

    @transform.setter
    def transform(self, value):
        if 'transform' in self.state:
            if isinstance(value, list):
                self.state['transform'].extend([TransformSpecification(v)
                                                for v in value])
            else:
                self.state['transform'].append(TransformSpecification(value))
        else:
            if isinstance(value, list):
                self.state['transform'] = [TransformSpecification(v)
                                           for v in value]
            else:
                self.state['transform'] = [TransformSpecification(value)]

    @property
    def truncate(self):
        if 'truncate' in self.state:
            return self.state['truncate']
        else:
            return None

    @truncate.setter
    def truncate(self, value):
        self.state['truncate'] = TruncateSpecification(value)

    @property
    def append(self):
        if 'append' in self.state:
            return self.state['append']
        else:
            return None

    @append.setter
    def append(self, value):
        if isinstance(value, basestring):
            self.state['append'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), str(value)))


class TransformSpecification(giza.libgiza.config.ConfigurationBase):
    @property
    def regex(self):
        return self.state['regex']

    @regex.setter
    def regex(self, value):
        if isinstance(value, basestring):
            try:
                self.state['regex'] = re.compile(value)
            except:
                pass

        if 'regex' not in self.state:
            raise TypeError('{0}: {1}'.format(type(value), str(value)))

    @property
    def replace(self):
        return self.state['replace']

    @replace.setter
    def replace(self, value):
        if isinstance(value, basestring):
            self.state['replace'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), str(value)))


class TruncateSpecification(giza.libgiza.config.ConfigurationBase):
    def ingest(self, input_obj):
        if input_obj is None:
            return

        if 'start-after' in input_obj:
            input_obj['start_after'] = input_obj['start-after']
            del input_obj['start-after']

        if 'end-before' in input_obj:
            input_obj['end_before'] = input_obj['end-before']
            del input_obj['end-before']

        super(TruncateSpecification, self).ingest(input_obj)

    @property
    def start_after(self):
        if 'start_after' in self.state:
            return self.state['start_after']
        else:
            return None

    @start_after.setter
    def start_after(self, value):
        if isinstance(value, basestring) or isinstance(value, int):
            self.state['start_after'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), str(value)))

    @property
    def end_before(self):
        if 'end_before' in self.state:
            return self.state['end_before']
        else:
            return None

    @end_before.setter
    def end_before(self, value):
        if isinstance(value, basestring) or isinstance(value, int):
            self.state['end_before'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), str(value)))
