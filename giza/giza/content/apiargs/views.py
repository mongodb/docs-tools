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

from rstcloth.rstcloth import RstCloth
from rstcloth.rstcloth import fill
from rstcloth.table import TableData, TableBuilder, ListTable

def setup_replacements(content):
    if content.interface == "command": 
        role_type = "dbcommand"
    elif content.interface == "method": 
        role_type = "method"
    elif content.interface == "phpmethod":
        role_type = "phpmethod"
    else: 
        role_type = "samp"

    if "role" not in content.replacement:
        content.replacement["role"] = RstCloth.role(role_type, content.operation)

    if "type" not in content.replacement: 
        if isinstance(content.type, list):
            if len(content.type) == 1: 
                content.replacement["type"] = content.type[0]
            elif len(content.type) == 2: 
                content.replacement["type"] = "or".join(content.type)
            else: 
                types = copy.copy(content.type)
                types[-1] = "and " + types[-1]
                content.replacement["type"] = ",".join(types)
        else: 
            content.replacement["type"] = content.type

    if "argname" not in content.replacement:
        content.replacement["argname"] = content.name
    

def render_apiargs(apiargs):
    for content in apiargs.ordered_content():
        setup_replacements(content)
        content.render() # run_replacements

    r = RstCloth()

    r.directive('only', '(html or singlehtml or dirhtml)')
    r.newline()
    render_apiarg_table(r, apiargs)

    r.newline()

    r.directive('only', '(texinfo or latex or epub)')
    r.newline()
    render_apiarg_fields(r, apiargs)

    return r


def render_apiarg_table(r, apiargs):
    table = TableData()

    header = [apiargs.field_type()]

    if apiargs.has_type() is True:
        header.append('Type')

    header.append('Description')

    num_columns = len(header)
    table.add_header(header)

    if num_columns == 2:
        widths = [20, 80]
        for entry in apiargs.ordered_content():
            table.add_row([RstCloth.pre(entry.name),
                           fill(string=entry.description, first=0, hanging=3, wrap=False)])
    elif num_columns == 3:
        widths = [20, 20, 80]
        for entry in apiargs.ordered_content():
            table.add_row([RstCloth.pre(entry.name),
                           entry.type_for_table_output(),
                           fill(string=entry.description, first=0, hanging=3, wrap=False)])

    r.content(TableBuilder(ListTable(table, widths=widths)).output, indent=3)


def render_apiarg_fields(r, apiargs):
    for content in apiargs.ordered_content():

        field_name = [content.arg_name]

        if content.type != '':
            field_name.append(', '.join(content.type))

        field_name.append(content.name)

        field_content = fill(string=content.description,
                             first=0,
                             hanging=6,
                             wrap=False)

        r.field(name=' '.join(field_name),
                value=field_content,
                indent=3,
                wrap=False)
        r.newline()
