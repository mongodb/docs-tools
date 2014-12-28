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

from giza.config.base import RecursiveConfigurationBase
from giza.tools.serialization import dict_from_list

class ReplacementData(RecursiveConfigurationBase):
    def ingest(self, input_obj): 
        input_obj = self._prep_load_data(input_obj)

        if isinstance(input_obj, dict):
            if 'edition' in input_obj and input_obj['edition'] == self.conf.project.edition:
                super(ReplacementData, self).intest(input_obj)
                return
            else:
                raise TypeError("replacement data is malformed given edition configuration.")
        elif not isinstance(input_obj, list):
            raise TypeError("replacement data must be a list or stream of documents.")
        else:
            mapping = dict_from_list('edition', input_obj)

            if self.conf.project.edition in mapping:
                if isinstance(mapping[self.conf.project.edition], dict):
                    self.state = mapping[self.conf.project.edition]
                else: 
                    TypeError("the replacements for the {0} edition are malformed".format(self.conf.project.edition))
            else: 
                raise TypeError("no replacements configured for edition: " + self.conf.project.edition)

    def items(self):
        return self.state.items()

    def keys(self):
        return self.state.keys()

    def values(self):
        return self.state.values()
