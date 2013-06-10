import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import expand_tree, get_branch, get_conf_file, ingest_yaml
from docs_meta import render_paths
from makecloth import MakefileCloth

m = MakefileCloth()
paths = render_paths('dict')

def generate_integration_targets(conf):
    dependencies = conf['targets']

    for dep in conf['doc-root']:
        dependencies.append(os.path.join(paths['public'], dep))

    for dep in conf['branch-root']: 
        if isinstance(dep, list):
            dep = os.path.sep.join(dep)

        if dep != '':
            dependencies.append(os.path.join(paths['branch-staging'], dep))
        else:
            dependencies.append(paths['branch-staging'])
    
    m.target('publish', dependencies)
    m.msg('[build]: deployed branch {0} successfully to {1}'.format(get_branch(), paths['public']))
    m.target('.PHONY', 'publish')

def main():
    conf_file = get_conf_file(__file__)
    generate_integration_targets(ingest_yaml(conf_file))
    
    m.write(sys.argv[1])
    print('[meta-build]: build "' + sys.argv[1] + '" to specify integration targets.')

if __name__ == '__main__':
    main()
