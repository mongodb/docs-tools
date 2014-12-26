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

from rstcloth.rstcloth import RstCloth

def get_replacements(conf): 
    if "replacement" in conf.system.data.files:
        mapping = conf.system.data.files.replacement
    elif "replacements" in conf.system.data.files::
        mapping = conf.system.data.files.replacements
    else:
        return []
        
    r = RstCloth()

    for k, v in mapping.items():
        r.replacement(k, v)
    
    return r.data
