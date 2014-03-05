#!/usr/bin/python

import sys
import os.path
from multiprocessing import cpu_count
import pkg_resources

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from utils.output import build_platform_notification
from utils.serialization import ingest_yaml
from utils.config import get_conf, get_conf_file, get_sphinx_builders

from makecloth import MakefileCloth

# to add a symlink build process, add a tuple to the ``links`` in the builder definitions file.

m = MakefileCloth()

conf = get_conf()

def make_all_sphinx(config):
    b = 'prereq'

    m.section_break('sphinx prerequisites')
    m.newline()

    m.comment('content generators')
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
    m.target(['prereq', 'sphinx-prerequisites'], block=b)
    m.job('fab sphinx.prereq', block=b)

    build_source_dir = conf.paths.branch_output + '/source'

    if 'generate-source' in config and config['generate-sourced']:
        m.target('generate-source', ['setup'], config['generate-sourced'], block=b)
        m.job('fab generate.source')

    m.section_break('sphinx targets', block=b)
    m.newline(block=b)

    sphinx_targets = []

    targets = []
    for builder in get_sphinx_builders():
        if 'tags' in config:
            builder_targets = []
            for tag in config['tags']:
                tag_target = '-'.join([builder, tag])

                builder_targets.append(tag_target)
                targets.append(tag_target)

                if not 'generated-source' in config:
                    m.target(tag_target, 'generate-source-' + tag)

            m.target(builder, builder_targets)
        else:
            targets.append(builder)

    if 'sphinx_builders' in config:

        for target in config['sphinx_builders']:
            m.target(target)
            m.job('fab sphinx.target:{0}'.format(','.join([target + '-hosted', target + '-saas'])))

        m.newline()

    for builder in targets:
        sphinx_targets.extend(sphinx_builder(builder))

    m.section_break('meta', block='footer')
    m.newline(block='footer')
    m.target('.PHONY', sphinx_targets, block='footer')
    m.target('.PHONY', [ 'api', 'toc', 'intersphinx', 'images', 'tables'], block='footer')

def sphinx_builder(target):
    b = 'production'
    m.comment(target, block=b)

    fab_prefix = 'fab'
    ret_value = [ target ]
    fab_arg = [target]

    target_parts = target.split('-')

    if len(target_parts) > 3:
        raise Exception('[meta-build]: Invalid sphinx builder: ' + target)
    elif len(target_parts) == 1:
        builder = target
        clean_target = '-'.join(['clean', builder])
        ret_value.append(clean_target)

        m.target(clean_target, block=b)
        m.job('fab clean.sphinx:{0}'.format(builder), block=b)
        m.newline(block=b)
    elif len(target_parts) <= 3 and len(target_parts) > 1:
        if target[1] == 'hosted' or target[1] == 'saas':
            fab_prefix += " sphinx.edition:" + target[1]

            builder = target[0]

            fab_arg.append('tag=' + target[1])
            if target[1] == 'hosted':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1], utils.get_branch()))
            elif target[1] == 'saas':
                fab_arg.append('root=' + os.path.join(paths['output'], target[1]))

    # m.target(target, 'sphinx-prerequisites', block=b)
    # m.job(fab_prefix + ' sphinx.build:' + ','.join(fab_arg), block=b)
    # if target.endswith('saas') or target.endswith('hosted'):
    #     m.target(target, 'generate-source', block=b)
    # else:
    m.target(target, block=b)

    if target == 'gettext' or 'gettext' in target:
        m.job('{0} tx.update'.format(fab_prefix), block=b)
    else:
        m.job('{0} sphinx.target:{1}'.format(fab_prefix, target), block=b)

    m.job(build_platform_notification('Sphinx', 'completed {0} build.'.format(target)), ignore=True, block=b)

    return ret_value

def main():
    config = ingest_yaml(get_conf_file(file=__file__, directory=conf.paths.builddata))

    make_all_sphinx(config)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify sphinx builders.')

if __name__ == '__main__':
    main()
