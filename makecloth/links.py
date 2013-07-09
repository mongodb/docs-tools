#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

import utils
from makecloth import MakefileCloth
from docs_meta import render_paths

# to add a symlink build process, add a tuple to the ``links`` in the builder definitions file.

m = MakefileCloth()
paths = render_paths('dict')

def make_all_links(links):
    m.comment('each link is created in the root and then moved into place using the "create-link" script.', block='header')
    m.newline(block='header')

    all_links = []
    phony = ['links', 'clean-links', '{0}/manual'.format(paths['public'])]
    for link in links:
        block = link['type']
        link_path = link['link-path']

        all_links.append(link_path)
        if block == 'content':
            phony.append(link_path)

        m.target(link_path, block=block)
        m.job(job='fab process.input:{0} process.output:{1} process.create_link'.format(link['referent'], link_path), block=block)
        m.newline(block=block)

    m.comment('meta-targets for testing/integration with rest of the build. must apear at the end', block='footer')
    m.newline(block='footer')

    m.target('.PHONY', phony, block='footer')
    m.target('links', all_links, block='footer')
    m.newline(block='footer')
    m.target('clean-links', block='footer')
    m.job('rm -rf {0}'.format(' '.join(phony)), True)

def main():
    conf_file = utils.get_conf_file(__file__)
    make_all_links(utils.ingest_yaml_list(conf_file))

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify symlink builders.')

if __name__ == '__main__':
    main()
