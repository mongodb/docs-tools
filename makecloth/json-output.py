#!/usr/bin/python

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from docs_meta import get_manual_path, render_paths, get_conf
from makecloth import MakefileCloth

def generate_meta():
    m = MakefileCloth()
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

    return m

def main():
    m = generate_meta()

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify json output.')

if __name__ == '__main__':
    main()
