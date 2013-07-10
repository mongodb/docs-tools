#!/usr/bin/python

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

import utils
from docs_meta import get_manual_path, render_paths, conf
from makecloth import MakefileCloth

paths = render_paths('dict')

if conf.git.remote.upstream.endswith('ecosystem'):
    paths['public-json-output'] = os.path.join(paths['public'], 'json')
    conf.build.url = 'http://docs.mongodb.org/ecosystem'
else:
    paths['public-json-output'] = os.path.join(paths['branch-staging'], 'json')
    conf.build.url = '/'.join(['http://docs.mongodb.org', conf.git.branches.current])

paths['build-json-output'] = os.path.join(paths['branch-output'], 'json')
paths['branch-json-list-file'] = os.path.join(paths['branch-output'], 'json-file-list')
paths['public-json-list-file'] = os.path.join(paths['public-json-output'], '.file_list')

m = MakefileCloth()

def generate_meta():
    m.section_break('meta')

    m.target('json-output', ['json'])
    m.job('fab process.all_json_output')

    rsync_cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {0}/ {1}'
    m.job(rsync_cmd.format(paths['build-json-output'], paths['public-json-output']))
    m.msg('[json]: migrated all .json files to staging.')
    m.msg('[json]: processed all json files.')

    m.section_break('list file')

    m.comment('the meta build system generates "{0}" when it generates this file'.format(paths['branch-json-list-file']))

    fab_cmd = 'fab process.input:{0} process.output:{1} process.copy_if_needed:json'
    m.target('json-file-list', paths['public-json-list-file'])
    m.target(paths['public-json-list-file'], 'json-output')
    m.job(fab_cmd.format(paths['branch-json-list-file'] , paths['public-json-list-file']))
    m.msg('[json]: rebuilt inventory of json output.')

    m.target(paths['build-json-output'], 'json')

    m.target('.PHONY', ['clean-json-output', 'clean-json', 'json-output', 'json-file-list'])
    m.target('clean-json-output', 'clean-json')
    m.job(' '.join(['rm -rf ', paths['public-json-list-file'], paths['branch-json-list-file'], paths['public-json-output']]))
    m.msg('[json]: removed all processed json.')

def get_source_name(fn):
    path = fn.split(os.path.sep)[3:]
    path[-1] = '.'.join([os.path.splitext(path[-1])[0], 'txt'])
    path = os.path.sep.join(path)
    return os.path.join('source', path)

def main():
    generate_meta()

    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" to specify json output.')

if __name__ == '__main__':
    main()

