import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import expand_tree
from docs_meta import render_paths
from makecloth import MakefileCloth

m = MakefileCloth()
paths = render_paths('dict')

def generate_table_build_rules():
    m.section_break('generated table build rules')
    list_tables = []
    rst_tables = []
    for source in expand_tree(paths['includes'], 'yaml'):
        if os.path.basename(source).startswith('table'):
            m.comment('standard rst table')
            target = '.'.join([os.path.splitext(source)[0], 'rst'])
            m.target(target, source)
            m.job('$(PYTHONBIN) {0}/rstcloth/table.py {1} {2}'.format(paths['buildsystem'], source, target))
            m.msg('[tables]: regenerated {0}'.format(target))
            m.newline()

            rst_tables.append(target)
            
            m.comment('list table')
            target = '.'.join([os.path.splitext(source)[0] + '-list', 'rst'])
            m.target(target, source)
            m.job('$(PYTHONBIN) {0}/rstcloth/table.py {1} {2} --type list'.format(paths['buildsystem'], source, target))
            m.msg('[tables]: regenerated {0}'.format(target))
            m.newline()

            list_tables.append(target)
    
    targets = rst_tables + list_tables
    m.section_break('meta targets for generated tables')
    m.target('tables', targets)
    m.target('rst-tables', rst_tables)
    m.target('list-tables', list_tables)
    m.target('clean-tables')
    m.job('rm -f ' + ' '.join(targets), ignore=True)
    m.msg('[tables-clean]: removed all generated tables.')
    m.target('.PHONY', 'rst-tables list-tables tables clean-tables')
    
def main():
    generate_table_build_rules()
    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" for generated tables.')

if __name__ == '__main__':
    main()
