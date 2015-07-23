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

logger = logging.getLogger('giza.content.newTables.views')


def render_table(rows):
    r = RstCloth()

    r.directive(name="list-table", fields=[("header-rows", "1")])
    r.newline()

    firstRow = True

    for row in rows.ordered_content():
        firstField = True

        if firstRow:
            columnCount = len(row.fields)
        else:
            checkColumns = len(row.fields)
        if checkColumns != columnCount:
            break

        for field in row.fields:
            if firstField:
                r.content("* - "+field, wrap=False, indent=3)
                r.newline()
                firstField = False
            else:
                r.content("- "+field, wrap=False, indent=5)
                r.newline()
            firstRow = False
    return r
