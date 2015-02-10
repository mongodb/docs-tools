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

from libgiza.config import ConfigurationBase
from giza.content.helper import edition_check

logger = logging.getLogger('giza.config.redirects')


def redirect_path_spec_normalization(value):
    o = []
    if not value.startswith('/'):
        o.append('/')

    if value.endswith('/'):
        value = value[:-1]

    o.append(value)

    return ''.join(o)


class RedirectSpecification(ConfigurationBase):
    _option_registry = ['type', 'external', 'edition']

    def __gettattr__(self, key):
        if key == 'from':
            key = 'from_loc'

        super(RedirectSpecification, self).__getattr__(key)

    def __setattr__(self, key, value):
        if key == 'from':
            key = 'from_loc'

        super(RedirectSpecification, self).__setattr__(key, value)

    @property
    def from_loc(self):
        return ''.join([self.output[0], self.state['from']])

    @from_loc.setter
    def from_loc(self, value):
        self.state['from'] = redirect_path_spec_normalization(value)

    @property
    def to(self):
        return ''.join([self.output[1], self.state['to']])

    @to.setter
    def to(self, value):
        self.state['to'] = redirect_path_spec_normalization(value)

    @property
    def code(self):
        if 'code' in self.state:
            return self.state['code']
        else:
            return 303

    @code.setter
    def code(self, value):
        if value in (301, 302, 303, 307, 308):
            self.state['code'] = value
        else:
            raise TypeError

    @property
    def output(self):
        left, right = self.state['output']

        if left in ('', '/'):
            pass
        elif left != '/' and not left.startswith('/') and not left.startswith('http'):
            left = '/' + left

        if right == '/':
            right = ''
        elif not right.startswith('/') and not right.startswith('http'):
            right = '/' + right

        return left, right

    @output.setter
    def output(self, value):
        if isinstance(value, dict):
            o = value.items()[0]
        elif isinstance(value, tuple) and len(value) == 2:
            o = value
        elif not isinstance(value, list):
            o = (value, value)
        else:
            raise TypeError

        self.state['output'] = o

    def dict(self):
        return {
            'from': self.state['from'],
            'to': self.state['to'],
            'code': self.code,
            'output': self.output,
            'external': self.external if 'external' in self.state else ''
        }


class HtaccessData(list):

    def append(self, item):
        self.insert(-1, item)

    def extend(self, items):
        for item in items:
            self.insert(-1, item)

    def insert(self, index, item):
        if item is None:
            return
        elif edition_check(item, self.conf) is False:
            return

        outputs = resolve_outputs_for_redirect(item['outputs'], self.conf)

        for doc in process_redirect_inputs(outputs, item):
            super(HtaccessData, self).insert(index, RedirectSpecification(doc))


def is_computed_output(key):
    if isinstance(key, (tuple, list)):
        key = key[0]

    if key == 'all' or key.startswith('before') or key.startswith('after'):
        return True
    else:
        return False

# Redirect Resolution

# the following three private functions are refactored components of
# ``resolve_output_for_redirect()``


def _add_outputs_to_computed(computed, keyword, base, conf):
    if keyword == 'all':
        computed.extend(conf.git.branches.published)
    elif keyword == 'before':
        computed.extend(conf.git.branches.published[conf.git.branches.published.index(base):])
    elif keyword == 'after':
        computed.extend(conf.git.branches.published[:conf.git.branches.published.index(base)])


def _render_key(sub_key, left_base, right_base):
    if sub_key == left_base:
        left = sub_key
    else:
        left = '/'.join([left_base, sub_key])

    if sub_key == right_base:
        right = sub_key
    else:
        right = '/'.join([right_base, sub_key])

    return left, right


def _get_redirect_base_paths(computed, out, conf):
    if out == 'all':
        out_key = out_value = ''
        _add_outputs_to_computed(computed, 'all', 0, conf)
    elif isinstance(out, dict):
        out_key, out_value = out.items()[0]
        if isinstance(out_value, dict):
            # for mms where from/to paths are mapped differently
            if '-' in out_key:
                keyword, base = out_key.split('-', 1)
            else:
                keyword = out_key
                base = ''
            out_key, out_value = out_value.items()[0]
            _add_outputs_to_computed(computed, keyword, base, conf)
    else:
        if out == []:
            out_key = out_value = ''
        elif is_computed_output(out):
            keyword, base = out.split('-', 1)
            out_key = out_value = ''
            _add_outputs_to_computed(computed, keyword, base, conf)
        elif isinstance(out, tuple):
            out_key, out_value = out
        else:
            out_key = out_value = out

    return out_key, out_value

# The following functions describe the process for inserting documents into the
# HtaccessData list and are called in HtaccessData.list()


def resolve_outputs_for_redirect(outputs, conf):
    if 'integration' in conf.system.files.data:
        shadows = conf.system.files.data.integration['base']['links']
    else:
        shadows = []

    expanded_outputs = []
    for out in outputs:
        computed = []

        out_key, out_value = _get_redirect_base_paths(computed, out, conf)

        for shadow in shadows:
            key, value = shadow.items()[0]
            if value == out_value:
                expanded_outputs.extend((value, key))

        expanded_outputs.extend([_render_key(o, out_key, out_value) for o in computed])

    outputs.extend(expanded_outputs)
    return outputs


def process_redirect_inputs(outputs, item):
    docs = []

    if len(outputs) == 0:
        docs.append(item)
    elif len(outputs) == 1:
        item['output'] = item['outputs'][0]
        del item['outputs']
        docs.append(item)
    else:
        for out in item['outputs']:
            if isinstance(out, dict):
                output = out.items()[0]
            elif isinstance(out, tuple) and len(out) == 2:
                output = out
            else:
                output = (out, out)

            if is_computed_output(output[0]):
                continue

            redir = {'output': output}
            redir.update(item)
            del redir['outputs']
            docs.append(redir)

    return docs
