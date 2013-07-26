#!/usr/bin/python

import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

import utils
from makecloth import MakefileCloth
from docs_meta import conf
m = MakefileCloth()

def build_all_sphinx_migrations(migrations):
    links = { 'phony': [], 'all': [] }
    for migration in migrations:
        block = migration['action']

        if 'dependency' not in migration:
            migration['dependency'] = None

        if block == 'link':
            m.target(target=migration['target'],
                     block=block)
        else:
            m.target(target=migration['target'],
                     dependency=migration['dependency'],
                     block=block)

        if block == 'touch':
            m.job('touch {0}'.format(migration['target']), block=block)
            m.msg('[build]: touched {0} to ensure proper migration'.format(migration['target']), block=block)
            m.newline(block=block)
        elif block == 'dep':
            m.newline(block=block)
        elif block == 'transfer':
            if 'branch' not in migration or migration['branch'] == conf.git.branches.current:
                m.job('mkdir -p {0}'.format(migration['target']))
                m.job('rsync -a {0}/ {1}/'.format(migration['dependency'], migration['target']))

                if 'filter' in migration and migration['filter'] and migration['filter'] is not None:
                    fsobjs = [ ]
                    for obj in migration['filter']:
                        fsobjs.append(migration['target'] + obj)
                    m.job('rm -rf {0}'.format(' '.join(fsobjs)))

                m.job('touch {0}'.format(migration['target']), block=block)
                m.msg('[build]: migrated "{0}" to "{1}"'.format(migration['dependency'], migration['target']))
            else:
                m.msg('[build]: doing nothing for {0} in this branch'.format(migration['target']))
        elif block == 'cp':
            target_array = migration['target'].rsplit('/', 1)
            block= '-'.join([block, migration['type']])

            if len(target_array) > 1:
                m.job('mkdir -p ' + target_array[0], block=block)

            m.job('cp {0} {1}'.format(migration['dependency'], migration['target']), block=block)
            m.msg('[build]: migrated "{0}" to "{1}"'.format(migration['dependency'], migration['target']))
            m.newline(block=block)
        elif block == 'link':
            m.job(job='fab process.input:{0} process.output:{1} process.create_link'.format(migration['dependency'], migration['target']), block=block)
            m.newline(block=block)
            links['all'].append(migration['target'])
            
            if migration['type'] == 'phony':
                links['phony'].append(migration['target'])
        elif block == 'cmd':
            if isinstance(migration['command'], list):
                for cmd in migration['command']:
                    m.job(cmd)
            else:
                m.job(migration['command'])

            if 'message' in migration:
                m.msg(migration['message'])

            if 'phony' in migration:
                links['phony'].append(migration['target'])
        elif block == 'mkdir':
            m.job('mkdir -p $@')
            m.msg('[build]: created $@')

    m.newline(block='footer')
    m.target('.PHONY', links['phony'], block='footer')
    m.target('links', links['all'], block='footer')
    m.newline(block='footer')
    m.target('clean-links', block='footer')
    m.job('rm -rf {0}'.format(' '.join(links['all'])), True)

def main():
    conf_file = utils.get_conf_file(__file__)
    build_all_sphinx_migrations(utils.ingest_yaml(conf_file))

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify sphinx migrations.')

if __name__ == '__main__':
    main()
