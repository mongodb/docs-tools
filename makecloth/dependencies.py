#!/usr/bin/python

import re
import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))

from utils import expand_tree
from makecloth import MakefileCloth

m = MakefileCloth()

def fix_include_path(inc, fn, source):
    if inc.startswith('/'):
        return source + inc
    else:
        return os.path.join(os.path.dirname(os.path.abspath(fn)), fn)

def generate_build_system(source):
    files = expand_tree(source, 'txt')

    inc_pattern = re.compile(r'\.\. include:: (.*\.(?:txt|rst))')

    dep_info = []

    for fn in files:
        includes = []
        try:
            with open(fn, 'r') as f:
                for line in f:
                    r = inc_pattern.findall(line)
                    if r:
                        includes.append(fix_include_path(r[0], fn, source))
            if len(includes) >= 1:
                dep_info.append( { 't': fn, 'd': includes } )
        except IOError
            continue

    composite_files = []
    for dep in dep_info:
        t = dep['t']
        d = dep['d']

        composite_files.append(t)
        m.target(t, d)
        m.job('fab process.update_time:{0}'.format(t), block='deps')
        m.msg('[dependency]: updated timestamp of {0} because its included files changed'.format(t), block='deps')

    m.target('composites', composite_files)

def main():
    generate_build_system('source')

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies on included files.')

if __name__ == '__main__':
    main()
