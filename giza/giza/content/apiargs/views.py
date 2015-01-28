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

from rstcloth.rstcloth import RstCloth
from rstcloth.rstcloth import fill
from rstcloth.table import TableData, TableBuilder, ListTable

field_type = {
    'param' : 'Parameter',
    'field': 'Field',
    'arg': 'Argument',
    'option': 'Option',
    'flag': 'Flag',
}

def render_apiargs(apiargs, conf):
    r = RstCloth()

    r.directive('only', '(html or singlehtml or dirhtml)')
    render_apiarg_table(r, apiargs)

    r.directive('only', '(texinfo or latex or epub)')
    render_apiarg_fields(r, apiargs)

    return r

def render_apiarg_table(r, apiargs):
    table = TableData()

    header = [ apiargs.field_type() ]

    if apiargs.has_type() is True:
        header.append('Type')

    header.append('Description')

    num_columns = len(header)
    table.add_header(header)

    if num_columns == 2:
        widths = [ 20, 80 ]
        for entry in apiargs.ordering:
            table.add_row([RstCloth.pre(entry.name),
                           entry.description])
    elif num_columns == 3:
        widths = [ 20, 20, 80 ]
        for entry in apiargs.ordering:
            table.add_row([RstCloth.pre(entry.name),
                           entry.type_for_table_output(),
                           entry.description])

    r.content(TableBuilder(ListTable(table, widths=widths)).output, indent=3)

def render_apiarg_fields(r, apiargs):
    pass
