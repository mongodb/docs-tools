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
import sys
import logging
import numbers
import collections

import libgiza.config
import giza.content.helper

logger = logging.getLogger('giza.config.images')

if sys.version_info >= (3, 0):
    basestring = str


class ImageData(list):
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

        super(ImageData, self).insert(index, ImageSpecification(item, self.conf))


class ImageSpecification(libgiza.config.RecursiveConfigurationBase):
    @property
    def name(self):
        return self.state['name']

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self.state['name'] = value
            self.state['source_base'] = os.path.join(self.conf.paths.projectroot,
                                                     self.conf.paths.branch_images, value)
            self.state['source_core'] = os.path.join(self.conf.paths.projectroot,
                                                     self.conf.paths.images, value + '.svg')
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def alt(self):
        return self.state['alt']

    @alt.setter
    def alt(self, value):
        if isinstance(value, basestring):
            self.state['alt'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def outputs(self):
        if 'outputs' in self.state:
            return self.state['outputs']
        else:
            return []

    @outputs.setter
    def outputs(self, value):
        if 'outputs' not in self.state:
            self.state['outputs'] = []

        if isinstance(value, collections.Iterable):
            self.state['outputs'].extend([ImageOutputSpecification(d, self) for d in value])
        else:
            self.state['outputs'].append(ImageOutputSpecification(value, self))

    output = outputs

    @property
    def dir(self):
        return self.conf.paths.branch_images

    @property
    def source_base(self):
        return self.state['source_base']

    @property
    def source_core(self):
        return self.state['source_core']

    @property
    def source_file(self):
        return self.source_base + '.svg'

    @property
    def rst_file(self):
        return self.source_base + '.rst'


class ImageOutputSpecification(libgiza.config.RecursiveConfigurationBase):
    @property
    def type(self):
        if 'type' in self.state:
            return self.state['type']
        else:
            return 'web'

    @type.setter
    def type(self, value):
        possible_types = ('print', 'target', 'web', 'offset')

        if value in possible_types:
            self.state['type'] = value
        else:
            raise TypeError("{0} is not in {1}".format(value, possible_types))

    @property
    def tag(self):
        if 'tag' in self.state:
            return self.state['tag']
        else:
            return None

    @tag.setter
    def tag(self, value):
        if isinstance(value, basestring):
            self.state['tag'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def target(self):
        if 'target' in self.state:
            return self.state['target']
        else:
            return None

    @target.setter
    def target(self, value):
        if isinstance(value, basestring):
            self.state['target'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def dpi(self):
        if 'dpi' in self.state:
            return self.state['dpi']
        else:
            return 96

    @dpi.setter
    def dpi(self, value):
        if isinstance(value, numbers.Number):
            self.state['dpi'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def width(self):
        if 'width' in self.state:
            return self.state['width']
        else:
            return None

    @width.setter
    def width(self, value):
        if isinstance(value, numbers.Number):
            self.state['width'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def scale(self):
        if 'scale' in self.state:
            return self.state['scale']
        else:
            return None

    @scale.setter
    def scale(self, value):
        if isinstance(value, numbers.Number) and 100 >= value >= 0:
            self.state['scale'] = value
        else:
            raise TypeError('{0}: {1}'.format(type(value), value))

    @property
    def build_type(self):
        if self.type == 'offset':
            return 'eps'
        else:
            return 'png'

    @property
    def output(self):
        if 'output' not in self.state:
            fn = [self.conf.source_base]

            if self.tag is not None:
                fn.extend(['-', self.tag])

            fn.extend(['.', self.build_type])

            self.state['output'] = ''.join(fn)

        return self.state['output']
