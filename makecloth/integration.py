import sys
import os.path
from copy import copy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import expand_tree, get_branch, get_conf_file, ingest_yaml
from docs_meta import render_paths, get_conf
from makecloth import MakefileCloth

m = MakefileCloth()
paths = render_paths('dict')

def generate_integration_targets(conf):
    dependencies = copy(conf['targets'])

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


def gennerate_translation_integration_targets(language, conf):
    dependencies = [ l + '-' + language for l in conf['targets'] ]

    for dep in conf['doc-root']:
        dependencies.append(os.path.join(paths['public'], dep))

    for dep in conf['branch-root']:
        if isinstance(dep, list):
            dep = os.path.sep.join(dep)

        if dep != '':
            dependencies.append(os.path.join(paths['branch-staging'], dep))
        else:
            dependencies.append(paths['branch-staging'])

    package_target = '-'.join(['package', language])
    publish_target = '-'.join(['publish', language])

    m.target(package_target)
    m.job('fab stage.package:' + language)

    m.target(publish_target, dependencies)
    m.msg('[build]: deployed branch {0} successfully to {1}'.format(get_branch(), paths['public']))
    m.newline()

    m.target('.PHONY', [publish_target, package_target])

def main():
    conf_file = get_conf_file(__file__)

    config = ingest_yaml(conf_file)

    if 'base' in config:
        generate_integration_targets(config['base'])

        for lang, lang_config in config.iteritems():
            if lang == 'base':
                continue

            if 'inherit' in lang_config:
                new_config = config[lang_config['inherit']]
                new_config.update(lang_config)

                gennerate_translation_integration_targets(lang, new_config)
            else:
                gennerate_translation_integration_targets(lang, lang_config)
    else:
        generate_integration_targets(config)

    m.write(sys.argv[1])
    print('[meta-build]: build "' + sys.argv[1] + '" to specify integration targets.')

if __name__ == '__main__':
    main()
