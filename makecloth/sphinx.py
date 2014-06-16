#!/usr/bin/python

import sys
import os.path
from multiprocessing import cpu_count
import pkg_resources

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from utils.output import build_platform_notification
from utils.serialization import ingest_yaml
from utils.config import get_conf, get_conf_file, get_sphinx_builders, render_sphinx_config

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
    m.job('fab log.set:debug generate.api')

    m.target('steps')
    m.job('fab log.set:debug generate.steps')

    m.target('intersphinx')
    m.job('fab log.set:debug sphinx.intersphinx')

    m.target('toc')
    m.job('fab log.set:debug generate.toc')

    m.target('tables')
    m.job('fab log.set:debug generate.tables')

    m.target('images')
    m.job('fab log.set:debug generate.images')

    m.target('releases')
    m.job('fab log.set:debug generate.releases')

    m.target('manual-pdfs', 'latex')
    m.job('fab log-set:debug process.pdfs')

    m.target('json-output', 'json')
    m.job('fab log.set:debug process.json_output')

    m.newline()
    m.comment('sphinx prereq integration.')
    m.target(['prereq', 'sphinx-prerequisites'], block=b)
    m.job('fab log.set:debug sphinx.prereq', block=b)

    build_source_dir = conf.paths.branch_output + '/source'

    if 'generate-source' in config and config['generate-sourced']:
        m.target('generate-source', ['setup'], config['generate-sourced'], block=b)
        m.job('fab log.set:debug generate.source')

    m.section_break('sphinx targets', block=b)
    m.newline(block=b)

    sphinx_targets = []

    targets = []
    for builder in get_sphinx_builders():
        if builder.endswith('base') or builder.startswith('editions'):
            continue

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
        builder_string = ','.join(['{0}-' + ed for ed in config['editions']])

        for target in config['sphinx_builders']:
            m.target(target)
            m.job('fab sphinx.target:{0}'.format(builder_string.format(target)))
            m.target(target + '-debug')
            m.job('fab log.set:debug sphinx.target:{0}'.format(builder_string.format(target)))

        m.newline()

    for builder in targets:
        if 'base' in builder:
            continue
        sphinx_targets.extend(sphinx_builder(builder))

    m.section_break('meta', block='footer')
    m.newline(block='footer')
    m.target('.PHONY', sphinx_targets, block='footer')
    m.target('.PHONY', [ 'api', 'toc', 'intersphinx', 'images', 'tables'], block='footer')

def sphinx_builder(target):
    b = 'production'
    m.comment(target, block=b)

    ret_value = [ target ]
    fab_arg = [target]

    target_parts = target.split('-')

    if len(target_parts) > 3:
        print('[meta-build]: Invalid sphinx builder: ' + target)
    elif len(target_parts) == 1:
        builder = target
        clean_target = '-'.join(['clean', builder])
        ret_value.append(clean_target)

        m.target(clean_target, block=b)
        m.job('fab clean.sphinx:{0}'.format(builder), block=b)
        m.newline(block=b)
    elif len(target_parts) <= 3 and len(target_parts) > 1:
        builder = target[0]

    m.target(target, block=b)

    if target == 'gettext' or 'gettext' in target:
        m.job('fab tx.update', block=b)
    else:
        m.job('fab sphinx.target:{0}'.format(target), block=b)

    m.job(build_platform_notification('Sphinx', 'completed {0} build.'.format(target)), ignore=True, block=b)

    m.target(target + '-debug', block=b)
    ret_value.append(target + '-debug')

    if target == 'gettext' or 'gettext' in target:
        m.job('fab log.set:debug tx.update', block=b)
    else:
        m.job('fab log.set:debug sphinx.target:{0}'.format(target), block=b)

    m.job(build_platform_notification('Sphinx', 'completed {0} build.'.format(target)), ignore=True, block=b)

    return ret_value

def main():
    config = ingest_yaml(get_conf_file(file=__file__, directory=conf.paths.builddata))

    config = render_sphinx_config(config)

    make_all_sphinx(config)

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify sphinx builders.')

if __name__ == '__main__':
    main()
