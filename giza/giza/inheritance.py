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

import copy
import os

import giza.libgiza.inheritance
import giza.libgiza.config

import giza.content.helper

import giza.tools.files


class InheritanceReference(giza.libgiza.inheritance.InheritanceReference):

    @property
    def file(self):
        return self.state['file']

    @file.setter
    def file(self, value):
        fns = [os.path.join(self.conf.paths.projectroot,
                            self.conf.paths.branch_includes, value),
               os.path.join(self.conf.paths.projectroot,
                            self.conf.paths.branch_source, value),
               os.path.join(self.conf.paths.projectroot, value)]

        for fn in fns:
            if os.path.exists(fn):
                self.state['file'] = fn
                break

        if 'file' not in self.state:
            raise TypeError('file named {0} does not exist'.format(value))


class InheritableContentBase(giza.libgiza.inheritance.InheritableContentBase):
    _reference_type = InheritanceReference

    def get_default_replacement(self):
        if 'replacement' in self.conf.system.files.data:
            base = self.conf.system.files.data.replacement
            if isinstance(base, dict):
                base = copy.deepcopy(base)
            else:
                base = copy.deepcopy(base.dict())
        else:
            base = {}

        return base


class DataContentBase(giza.libgiza.inheritance.DataContentBase):
    edition_check = staticmethod(giza.content.helper.edition_check)
    content_class = InheritableContentBase


class DataCache(giza.libgiza.inheritance.DataCache):
    content_class = DataContentBase

    def create_output_dir(self):
        dirname = self.conf.system.content.get(self.content_type).output_dir
        if (self.content_type is not None and
                len(self) > 0 and
                not os.path.isdir(dirname)):

            giza.tools.files.safe_create_directory(dirname)
