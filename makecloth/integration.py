import sys
import os.path
from copy import copy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.files import expand_tree
from utils.git import get_branch
from utils.serialization import ingest_yaml
from utils.config import get_conf, get_conf_file

from makecloth import MakefileCloth

m = MakefileCloth()
paths = get_conf().paths

def generate_integration_targets(conf):
    dependencies = copy(conf['targets'])

    for dep in conf['doc-root']:
        dependencies.append(os.path.join(paths['public'], dep))

    dependencies.extend(proccess_branch_root(conf))

    m.target('package')
    m.job('fab stage.package')

    m.target('publish', dependencies)
    m.msg('[build]: deployed branch {0} successfully to {1}'.format(get_branch(), paths['public']))
    m.newline()

    m.target('.PHONY', ['publish', 'package'])


def proccess_branch_root(conf):
    dependencies = []

    if 'branch-root' in conf and conf['branch-root'] is not None:
        for dep in conf['branch-root']:
            if isinstance(dep, list):
                dep = os.path.sep.join(dep)

            if dep != '':
                dependencies.append(os.path.join(paths['branch-staging'], dep))
            else:
                dependencies.append(paths['branch-staging'])

    return dependencies

def gennerate_translation_integration_targets(language, conf):
    dependencies = [ l + '-' + language for l in conf['targets'] ]

    for dep in conf['doc-root']:
        dependencies.append(os.path.join(paths['public'], dep))

    dependencies.extend(proccess_branch_root(conf))

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
