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
    build_source_dir = paths['branch-output'] + '/source'

    m.section_break('sphinx prerequisites')
    m.newline()
    m.target('sphinx-prerequisites', config['prerequisites'], block=b)
    m.msg('[sphinx-prep]: build environment prepared for sphinx.', block=b)

    if 'generated-source' in config and config['generated-source']:
        config['generated-source'].insert(0, build_source_dir)
        m.target('generate-source',  config['generated-source'], block=b)
        m.job('rsync --recursive --times --delete source/ ' + build_source_dir, block=b)
        m.msg('[sphinx-prep]: updated source in ' + build_source_dir, block=b)
        info_note = 'Build in progress past critical phase.'
        m.job(utils.build_platform_notification('Sphinx', info_note), ignore=True, block=b)
        m.msg('[sphinx-prep]: INFO - ' + info_note, block=b)

    m.target(build_source_dir, block=b)
    m.job('mkdir -p ' + build_source_dir, block=b)
    m.msg('[sphinx-prep]: created ' + build_source_dir, block=b)

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

            m.target(builder, builder_targets)
        else:
            targets.append(builder)
            targets.append('-'.join([builder, 'nitpick']))

    for builder in targets:
        sphinx_targets.extend(sphinx_builder(builder))

    m.section_break('meta', block='footer')
    m.newline(block='footer')
    m.target('.PHONY', sphinx_targets, block='footer')

def sphinx_builder(target_str):
    b = 'production'
    m.comment(target_str, block=b)

    target = target_str.split('-')

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
        m.msg('[clean-{0}]: removed all files supporting the {0} build'.format(builder) )
        m.newline(block=b)
    elif len(target) <= 3 and len(target) > 1:
        if target[1] == 'hosted' or target[1] == 'saas':
            builder = target[0]

            if target[1] == 'hosted':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1], utils.get_branch()))
            elif target[1] == 'saas':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1]))

        if target[1] == 'nitpick' or target_str.endswith('-nitpick'):
            builder = target[0]
            fab_arg.append('nitpick=True')

    m.target(target_str, 'sphinx-prerequisites', block=b)
    m.job('fab sphinx.build:' + ','.join(fab_arg), block=b)
    m.job(utils.build_platform_notification('Sphinx', 'completed {0} build.'.format(target_str)), ignore=True, block=b)
    m.msg('[{0}]: completed {0} build.'.format(target_str))

    return ret_value

def main():
    config = utils.ingest_yaml(utils.get_conf_file(__file__))

    make_all_sphinx(config)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify sphinx builders.')

if __name__ == '__main__':
    main()
