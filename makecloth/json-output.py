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

def generate_list_file(outputs, path):
    with open(path, 'w') as f:
        for fn in outputs:
            url = [ conf.build.url, 'json' ]
            url.extend(fn.split('/', 3)[3:])

            f.write(''.join(['/'.join(url), '\n']))

def generate_json_target(source, output_file):
    m.target(source, 'json')
    m.target(output_file, get_source_name(output_file))
    m.target(output_file, source)
    m.job('fab process.input:{0} process.output:{1} process.json_output'.format(source, output_file))
    m.msg('[json]: generated a processed json file: ' + output_file)
    m.newline()

def generate_meta(outputs):
    m.section_break('meta')

    m.target('json-output', ['json', 'process-json-output'])
    m.target('process-json-output', outputs)

    if len(outputs) > 0:
        rsync_cmd = 'rsync --recursive --times --delete --exclude="*fjson" {0}/ {1}'
        m.job(rsync_cmd.format(paths['build-json-output'], paths['public-json-output']))
        m.msg('[json]: migrated all .json files to staging.')
    m.msg('[json]: processed all json files.')

    m.section_break('list file')

    m.comment('the meta build system generates "{0}" when it generates this file'.format(paths['branch-json-list-file']))

    fab_cmd = 'fab process.input:{0} process.output:{1} process.copy_if_needed:json'
    m.target('json-file-list', paths['public-json-list-file'])
    m.target(paths['branch-json-list-file'], [os.path.join(paths['output'], 'makefile.json-output'), paths['build-json-output']])
    m.target(paths['public-json-list-file'], [paths['branch-json-list-file'], 'process-json-output'] )
    m.job(fab_cmd.format(paths['branch-json-list-file'] , paths['public-json-list-file']))
    m.msg('[json]: rebuilt inventory of json output.')

    m.target(paths['build-json-output'], 'json')

    m.target('.PHONY', ['clean-json-output', 'clean-json', 'json-output'])
    m.target('clean-json-output', 'clean-json')
    m.job(' '.join(['rm -rf ', paths['public-json-list-file'], paths['branch-json-list-file'], paths['public-json-output']]))
    m.msg('[json]: removed all processed json.')

def get_source_name(fn):
    path = fn.split(os.path.sep)[3:]
    path[-1] = '.'.join([os.path.splitext(path[-1])[0], 'txt'])
    path = os.path.sep.join(path)
    return os.path.join('source', path)

def source_fn_transform(fn, builder='json', ext='fjson'):
    # 'source/reference/programs.txt' -> build/master/builder/reference/programs.fjson
    path = os.path.join(conf.build.paths.output,
                        conf.git.branches.current,
                        'json',
                        # 'source/reference/programs.txt' -> 'reference/programs'
                        os.path.splitext(fn.split(os.path.sep, 1)[1])[0])

    return utils.dot_concat(path, ext)

def main():
    source_files = [ source_fn_transform(i) for i in utils.expand_tree('source', 'txt') ]
    outputs = []

    for source in source_files:
        base_fn = source.split(os.path.sep, 2)[2].rsplit('.', 1)[0]
        output_file = utils.dot_concat(os.path.sep.join([paths['branch-output'], base_fn]), 'json')
        outputs.append(output_file)

        generate_json_target(source, output_file)

    generate_list_file(outputs, paths['branch-json-list-file'] )

    generate_meta(outputs)

if __name__ == '__main__':
    main()

    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" to specify json output.')
