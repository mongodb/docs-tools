#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

import utils
from makecloth import MakefileCloth

m = MakefileCloth()

def build_all_migrations(migrations):
    m.comment('targets to migrate all content to the production staging directory..', block='header')
    m.newline(block='header')

    for migration in migrations:
        target_array = migration['target'].rsplit('/', 1)
        block=migration['type']

        m.target(target=migration['target'],
                 dependency=migration['source'],
                 block=block)

        if len(target_array) > 1:
            m.job('mkdir -p ' + target_array[0], block=block)
        m.job('cp $< $@', block=block)
        m.msg('[build]: migrated $@', block=block)
        m.newline(block=block)


def main():
    conf_file = utils.get_conf_file(__file__)
    build_all_migrations(utils.ingest_yaml(conf_file))

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify production migrations.')

if __name__ == '__main__':
    main()
