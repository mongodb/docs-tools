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

from rstcloth.rstcloth import RstCloth
from giza.content.steps.views import render_action

logger = logging.getLogger('giza.content.extracts.views')


def render_extracts(extract):
    r = RstCloth()
    extract.render()

    indent = 0
    if 'only' in extract:
        r.directive('only', extract.only, indent=indent)
        r.newline()
        indent += 3

    if 'style' in extract:
        r.directive('rst-class', extract.style, indent=indent)
        r.newline()

    render_action(extract, indent=indent, level=extract.level, r=r)

    return r


def get_include_statement(include_file):
    r = RstCloth()
    r.newline()

    r.directive('include', include_file)
    r.newline()

    return '\n'.join(r.data)
