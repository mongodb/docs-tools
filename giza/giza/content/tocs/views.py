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
from rstcloth.table import TableBuilder, RstTable, TableData

logger = logging.getLogger('giza.content.tocs.views')


def render_toctree(toc_items, is_ref=False):
    r = RstCloth()

    r.directive('class', 'hidden')
    r.newline()
    r.directive('toctree', fields=[('titlesonly', '')], indent=3)
    r.newline()

    for entry in toc_items:
        if is_ref is False and 'name' in entry:
            r.content('{0} <{1}>'.format(entry.name, entry.file), indent=6, wrap=False)
        else:
            r.content(entry.file, indent=6, wrap=False)

    return r


def render_dfn_list(toc_items):
    r = RstCloth()

    r.directive('class', 'toc')
    r.newline()

    for entry in toc_items:
        entry.render()
        idnt = 3 * entry.level

        if entry.text_only is True:
            if 'name' in entry:
                r.definition(entry.name, entry.description, indent=idnt)
            else:
                r.content(entry.description, indent=idnt)
            r.newline()
        else:
            if 'name' in entry:
                dfn_heading = r.role('doc', "{0} <{1}>".format(entry.name, entry.file))
            else:
                dfn_heading = r.role('doc', entry.file)

            if 'description' in entry:
                description = entry.description
            else:
                description = ''

            r.definition(dfn_heading, description, indent=idnt)
            r.newline()

    return r


def render_toc_table(toc_items):
    table = TableData()

    table.add_header(['Name', 'Description'])
    for entry in toc_items:
        entry.render()
        if 'name' in entry:
            table.add_row([entry.name, entry.description])
        else:
            table.add_row([RstCloth.role('doc', entry.file), entry.description])

    return TableBuilder(RstTable(table))
