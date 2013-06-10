import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import expand_tree
from docs_meta import render_paths
from makecloth import MakefileCloth

m = MakefileCloth()
paths = render_paths('dict')

def generate_api_build_rules():
    m.section_break('reference yaml file conversion')
    targets = []
    for source in expand_tree('source/reference', 'yaml'):
        target = '.'.join([os.path.splitext(source)[0], 'rst'])
        m.target(target, source)
        m.job('$(PYTHONBIN) {0}/rstcloth/param.py {1} {2}'.format(paths['buildsystem'], source, target))
        m.newline()

        targets.append(target)
    
    m.section_break('api reference generation')
    m.target('api', targets)
    m.target('clean-api')
    m.job('rm -f ' + ' '.join(targets), ignore=True)
    m.msg('[api-clean]: removed generated api reference')
    m.target('.PHONY', 'api clean-api')
    
def main():
    generate_api_build_rules()
    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" for api reference.')

if __name__ == '__main__':
    main()
