import sys
import os.path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('makecloth.giza')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))

from makecloth import MakefileCloth

try:
    import giza
    from giza.config.helper import new_config
    from giza.serialization import ingest_yaml_doc
    from giza.strings import hyph_concat
except ImportError as e:
    giza = None
    print(e)

def main():
    m = MakefileCloth()
    conf = new_config()
    output_file = os.path.join(conf.paths.projectroot, conf.paths.output, 'makefile.giza_build')
    m.section_break('giza build integration')
    m.newline()

    m.section_break('content generation targets')
    for gen_target in [ 'api', 'assets', 'images', 'intersphinx', 'options',
                        'primer', 'steps', 'tables', 'toc']:
        m.target(hyph_concat('giza', gen_target))
        m.job('giza generate ' + gen_target)

        m.target(hyph_concat('giza', 'force', gen_target))
        m.job('giza --force ' + gen_target)
        m.newline()

    m.section_break('sphinx targets')

    sconf = ingest_yaml_doc(os.path.join(conf.paths.projectroot,
                                         conf.paths.builddata,
                                         'sphinx.yaml'))
    builders = [b for b in sconf
                if not b.endswith('base') and b not in
                ('prerequisites', 'generated-source', 'languages', 'editions')]
    if 'editions' in sconf:
        editions = sconf['editions']
    else:
        editions = []

    if 'root-base' in sconf and 'languages' in sconf['root-base']:
        languages = sconf['root-base']['languages']
    else:
        languages = []

    complete = []

    for builder in builders:
        if '-' in builder:
            builder = builder.split('-')[0]

        if builder in complete:
            continue

        m.comment(builder + ' targets')
        for edition in editions:
            m.target(hyph_concat('giza', builder, edition))
            m.job('giza sphinx --builder {0} --edition {1}'.format(builder, edition))

            for language in languages:
                m.target(hyph_concat('giza', builder, edition, language))
                m.job('giza sphinx --builder {0} --edition {1} --language {2}'.format(builder, edition, language))

        if len(editions) == 0:
            m.target(hyph_concat('giza', builder))
            m.job('giza sphinx --builder ' + builder)

            for language in languages:
                m.target(hyph_concat('giza', builder, language))
                m.job('giza sphinx --builder {0} --language {1}'.format(builder, language))
        else:
            m.target(hyph_concat('giza', builder))
            m.job('giza sphinx --builder {0} --edition {1}'.format(builder, ' '.join(editions)))

        m.newline()
        complete.append(builder)

    m.section_break('deploy targets')
    for ptarget in conf.system.files.data.push:
        name = ptarget['target']
        m.target(hyph_concat('giza', name))
        m.job('giza push --target ' + name)
        m.newline()

    m.write(output_file)
    print('[meta-build]: built "build/makefile.giza_build" to integrate giza')

if __name__ == '__main__':
    if giza is None:
        logger.warning('giza is not available. not generating makefile.')
    else:
        main()
