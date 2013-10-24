import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import expand_tree, get_branch, get_conf_file, ingest_yaml
from docs_meta import render_paths, get_conf
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

    m.target('package')
    m.job('fab stage.package')

    m.target('publish', dependencies)
    m.msg('[build]: deployed branch {0} successfully to {1}'.format(get_branch(), paths['public']))
    m.newline()

    m.target('.PHONY', ['publish', 'package'])

def generate_json_output_meta():
    """This is dead code, hanging around for a while just in case we need it. see fabfile/process.py"""

    m.section_break('json output coordination.')
    paths = render_paths('dict')

    if get_conf().git.remote.upstream.endswith('ecosystem'):
        public_json_output = os.path.join(paths['public'], 'json')
    else:
        public_json_output = os.path.join(paths['branch-staging'], 'json')

    build_json_output = os.path.join(paths['branch-output'], 'json')
    branch_json_list_file = os.path.join(paths['branch-output'], 'json-file-list')
    public_json_list_file = os.path.join(public_json_output, '.file_list')

    m.section_break('meta')

    m.target('json-output', ['json'])
    m.job('fab process.json_output')

    rsync_cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {0}/ {1}'
    m.job(rsync_cmd.format(build_json_output, public_json_output))
    m.msg('[json]: migrated all .json files to staging.')
    m.msg('[json]: processed all json files.')

    m.section_break('list file')

    m.comment('the meta build system generates "{0}" when it generates this file'.format(branch_json_list_file))

    fab_cmd = 'fab process.input:{0} process.output:{1} process.copy_if_needed:json'
    m.target('json-file-list', public_json_list_file)
    m.target(public_json_list_file, 'json-output')
    m.job(fab_cmd.format(branch_json_list_file , public_json_list_file))
    m.msg('[json]: rebuilt inventory of json output.')

    m.target(build_json_output, 'json')

    m.target('.PHONY', ['clean-json-output', 'clean-json', 'json-output', 'json-file-list'])
    m.target('clean-json-output', 'clean-json')
    m.job(' '.join(['rm -rf ', public_json_list_file, branch_json_list_file, public_json_output]))
    m.msg('[json]: removed all processed json.')

def main():
    conf_file = get_conf_file(__file__)
    generate_integration_targets(ingest_yaml(conf_file))

    m.write(sys.argv[1])
    print('[meta-build]: build "' + sys.argv[1] + '" to specify integration targets.')

if __name__ == '__main__':
    main()
