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

from rstcloth.rstcloth import RstCloth

logger = logging.getLogger('giza.content.glossary.views')


def render_glossary(terms):
    r = RstCloth()

    r.directive(name="glossary", fields=[("sorted", "")])
    r.newline()

    for term in terms.ordered_content():
        r.definition(term.term, term.definition, wrap=False, indent=3)

    return r
