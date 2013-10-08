#!/usr/bin/python

import sys
import os.path
from multiprocessing import cpu_count
import pkg_resources

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

import utils
from makecloth import MakefileCloth
from docs_meta import render_paths

# to add a symlink build process, add a tuple to the ``links`` in the builder definitions file.

m = MakefileCloth()

paths = render_paths('dict')

def make_all_sphinx(config):
    b = 'prereq'

    m.section_break('sphinx prerequisites')
    m.newline()

    m.comment('content generators')
    m.target('composites')
    m.job('fab process.refresh_dependencies')

    m.target('api')
    m.job('fab generate.api')

    m.target('steps')
    m.job('fab generate.steps')

    m.target('intersphinx')
    m.job('fab sphinx.intersphinx')

    m.target('toc')
    m.job('fab generate.toc')

    m.target('tables')
    m.job('fab generate.tables')

    m.target('images')
    m.job('fab generate.images')

    m.target('releases')
    m.job('fab generate.releases')

    m.target('manual-pdfs', 'latex')
    m.job('fab process.pdfs')

    m.target('json-output', 'json')
    m.job('fab process.json_output')

    m.newline()
    m.comment('sphinx prereq integration.')
    m.target('sphinx-prerequisites', block=b)
    m.job('fab sphinx.prereq', block=b)

    build_source_dir = paths['branch-output'] + '/source'

    if 'generate-source' in config and config['generate-sourced']:
        m.target('generate-source', ['setup'], config['generate-sourced'], block=b)
        m.job('fab generate.source')

    m.section_break('sphinx targets', block=b)
    m.newline(block=b)

    sphinx_targets = []

    targets = []
    for builder in config['builders']:
        if 'tags' in config:
            builder_targets = []
            for tag in config['tags']:
                tag_target = '-'.join([builder, tag])

                builder_targets.append(tag_target)
                targets.append(tag_target)
                targets.append('-'.join([builder, tag, 'nitpick']))

                if not 'generated-source' in config:
                    m.target(tag_target, 'generate-source-' + tag)

            m.target(builder, builder_targets)
        else:
            targets.append(builder)
            targets.append('-'.join([builder, 'nitpick']))

    for builder in targets:
        sphinx_targets.extend(sphinx_builder(builder))

    m.section_break('meta', block='footer')
    m.newline(block='footer')
    m.target('.PHONY', sphinx_targets, block='footer')
    m.target('.PHONY', ['composites', 'api', 'toc', 'intersphinx', 'images', 'tables'], block='footer')

def sphinx_builder(target_str):
    b = 'production'
    m.comment(target_str, block=b)

    target = target_str.split('-')

    fab_prefix = 'fab'
    ret_value = [ target_str ]
    fab_arg = [target[0]]

    if len(target) > 3:
        raise Exception('[meta-build]: Invalid sphinx builder: ' + target)
    elif len(target) == 1:
        builder = target_str
        clean_target = '-'.join(['clean', builder])
        ret_value.append(clean_target)

        m.target(clean_target, block=b)
        m.job('fab sphinx.clean sphinx.build:{0}'.format(builder), block=b)
        m.newline(block=b)
    elif len(target) <= 3 and len(target) > 1:
        if target[1] == 'hosted' or target[1] == 'saas':
            fab_prefix += " sphinx.edition:" + target[1]

            builder = target[0]

            fab_arg.append('tag=' + target[1])
            if target[1] == 'hosted':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1], utils.get_branch()))
            elif target[1] == 'saas':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1]))

        if target[1] == 'nitpick' or target_str.endswith('-nitpick'):
            fab_prefix += ' sphinx.nitpick'
            builder = target[0]

    m.target(target_str, 'sphinx-prerequisites', block=b)
    m.job(fab_prefix + ' sphinx.build:' + ','.join(fab_arg), block=b)
    m.job(utils.build_platform_notification('Sphinx', 'completed {0} build.'.format(target_str)), ignore=True, block=b)

    return ret_value

def main():
    config = utils.ingest_yaml(utils.get_conf_file(__file__))

    make_all_sphinx(config)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify sphinx builders.')

if __name__ == '__main__':
    main()
