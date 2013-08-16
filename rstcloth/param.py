import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))

import utils
from docs_meta import load_conf
from rstcloth import RstCloth
from rstcloth import fill
from table import TableData, TableBuilder, ListTable

field_type = {
    'param' : 'Parameter',
    'field': 'Field',
    'arg': 'Argument',
    'option': 'Option',
    'flag': 'Flag',
}

class ParamTable(TableData):
    def __init__(self, header=None, rows=None):
        if header is None:
            self.header = []
        else:
            self.header = header

        if rows is None:
            self.rows = []
        else:
            self.rows = rows

        self.num_rows = 0
        self.widths = None
        self.final = False

    def set_column_widths(self, doc):
        if self.has_type(doc):
            self.widths = [ 20, 20, 60 ]
            self.num_columns = 3
            self.type_column = True
        else:
            self.widths = [ 20, 80 ]
            self.num_columns = 2
            self.type_column = False

    @staticmethod
    def has_type(doc):
        if 'type' in doc and doc['type'] is not None or False:
            return True
        else:
            return False

def generate_param_table(params):
    table_data = ParamTable()

    table_data.set_column_widths(params[0])

    table_data.add_header(render_header_row(params[0],
                                            table_data.num_rows,
                                            table_data.type_column))

    for param in params:
        row = [ RstCloth().pre(param['name']) ]

        if table_data.type_column is True:
            row.append(process_type_cell(param['type'], 'table'))

        row.append(process_description(param['description'], param['field']['optional']))

        table_data.add_row(row)

    table = TableBuilder(ListTable(table_data, widths=table_data.widths))

    return table.output

def generate_param_fields(param):
    _name = [ param['field']['type'] ]

    if ParamTable.has_type(param):
        _name.append(process_type_cell(param['type'], 'field'))

    if param['name'] is not None:
        _name.append(param['name'])

    description = param['description']

    if isinstance( param['description'], list):
        field_content = fill('\n'.join(param['description']), 0, 6, False)
    else:
        field_content = fill(param['description'], 0, 6, True)

    return ' '.join(_name), field_content


def process_description(content, optional=False):
    if isinstance(content, list):
        if optional is True:
            content[0] = 'Optional.\n' + content[0]
        return content
    else:
        if optional is True:
            o = 'Optional. '
        else:
            o = ''
        return fill(o + content).split('\n')

def process_type_cell(type_data, output):
    if isinstance(type_data, list):
        if output == 'field':
            return ','.join(type_data)
        elif output == 'table':
            length = len(type_data)

            if length == 2:
                return ' or '.join(type_data)
            elif length > 2:
                tmp = type_data[:-1]
                tmp.append('or ' + type_data[-1])
                return ', '.join(tmp)

    else:
        return type_data

def render_header_row(param_zero, num_rows, type_column):
    o = [ field_type[param_zero['field']['type']] ]

    if type_column is True:
        o.append('Type')

    o.append('Description')

    return o

def populate_external_param(fn, basename, projectdir, sourcedir):
    if fn.startswith('/'):
        fn = os.path.join(sourcedir, fn[1:])

    try:
        ext_param = utils.ingest_yaml_list(fn)
    except OSError:
        fn = os.path.join(basename, fn)
        ext_param = utils.ingest_yaml_list(fn)
    except OSError:
        fn = os.path.join(projectdir, sourcedir, fn)
        ext_param = utils.ingest_yaml_list(fn)
    else:
        pass

    o = { }
    for param in ext_param:
        # leaving the object sub-document unmodified if we use it at some point,
        # we might need to modify here.
        o[param['name']] = param

    return fn, o

def generate_params(params, fn):
    r = RstCloth()
    lconf = load_conf()
    basename = os.path.basename(fn)

    params.sort(key=lambda p: p['position'])

    # Begin by generating the table for web output
    r.directive('only', '(html or singlehtml or dirhtml)', block='htm')
    r.newline(block='htm')

    # { filename: { $name: <param> } }
    ext_params = {}

    processed_params = []
    for param in params:
        if 'file' in param:
            if param['file'] not in ext_params:

                fn, ext = populate_external_param(param['file'],
                                                  basename,
                                                  lconf.build.paths.projectroot,
                                                  lconf.build.paths.source)
                ext_params[fn] = ext

            param = ext_params[lconf.build.paths.source + param['file']][param['name']]
        processed_params.append(param)
            
    r.content(generate_param_table(processed_params), indent=3, block='html')
    r.newline(block='htm')

    # Then generate old-style param fields for non-web output
    r.directive('only', '(texinfo or latex or epub)', block='tex')
    r.newline(block='tex')

    for param in processed_params:
        key, val = generate_param_fields(param)
        r.field(name=key, value=val, indent=3, wrap=False, block='tex')
        r.newline(block='tex')

    return r

def main():
    input_data = utils.ingest_yaml_list(sys.argv[1])
    r = generate_params(input_data, sys.argv[1])

    r.write(sys.argv[2])

    print('[api]: rebuilt "' + sys.argv[2] + '" parameter table.')

if __name__ == '__main__':
    main()
