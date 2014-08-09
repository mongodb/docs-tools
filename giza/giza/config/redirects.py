# 2014 MongoDB, Inc.
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

logger = logging.getLogger('giza.config.redirects')

from giza.config.base import ConfigurationBase
from giza.content.helper import edition_check

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
        return self.state['code']

    @code.setter
    def code(self, value):
        if value in (301, 302, 303, 307, 308):
            self.state['code'] = value
        else:
            raise TypeError

    @property
    def output(self):
        left, right = self.state['output']

        if not left.startswith('/'):
            left = '/' + left

        if not right.startswith('/'):
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

########## Redirect Resolution ##########

def _add_outputs_to_computed(computed, keyword, base, conf):
    if keyword == 'all':
        computed.extend(conf.git.branches.published)
    elif keyword == 'before':
        computed.extend(conf.git.branches.published[conf.git.branches.published.index(base):])
    elif keyword == 'after':
        computed.extend(conf.git.branches.published[:conf.git.branches.published.index(base)])




def resolve_outputs_for_redirect(outputs, conf):
    if 'integration' in conf.system.files.data:
        shadows = conf.system.files.data.integration[0]['base']['links']
    else:
        shadows = []

    for idx, out in enumerate(outputs):
        computed = []
        if out == 'all':
            branch_keyword = base = 'all'
            out_key = out_value = ''
            _add_outputs_to_computed(computed, 'all', 0, conf)
        elif isinstance(out, dict):
            out_key, out_value = out.items()[0]
            if isinstance(out_value, dict):
                # for mms where from/to paths are mapped differently
                keyword, base = out_key.split('-', 1)
                out_key, out_value = out_value.items()[0]
                _add_outputs_to_computed(computed, keyword, base, conf)
        else:
            if is_computed_output(out):
                keyword, base = out.split('-', 1)
                _add_outputs_to_computed(computed, keyword, base, conf)
                out_key = out_value = base
            else:
                out_key = out_value = out

        # for shadow in shadows:
        #     key, value = shadow.items()[0]
        #     if key == out_value:
        #         print key
        #         computed.extend((key, value))

        outputs.extend([ ('/'.join([out_key, o]), '/'.join([out_value, o])) for o in computed ])
        # print(outputs)

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

            redir = { 'output': output }
            redir.update(item)
            del redir['outputs']
            docs.append(redir)

    return docs
