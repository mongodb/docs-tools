#!/usr/bin/python

# Leaving this file here for backwards compatibility. Can be removed
# eventually. The composites target is generated in sphinx.py

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from makecloth import MakefileCloth

m = MakefileCloth()

def generate_build_system():
    m.target('composites')
    m.job('fab process.refresh_dependencies')
    m.target('.PHONY', 'composites')

def main():
    generate_build_system()

    m.write(sys.argv[1])

    print('[meta-build]: built "' + sys.argv[1] + '" to specify dependencies on included files.')

if __name__ == '__main__':
    main()
