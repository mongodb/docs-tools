#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from makecloth import MakefileCloth

from utils.git import get_branch, get_commit
from utils.config import get_conf
from utils.project import get_manual_path

def generate_meta(conf):
    m = MakefileCloth()

    m.section_break('branch/release meta', block='rel')
    m.var('manual-branch', conf.git.branches.manual, block='rel')
    m.var('current-branch', str(get_branch()), block='rel')
    m.var('last-commit', str(get_commit()), block='rel')
    m.var('current-if-not-manual', conf.git.branches.manual, block='rel')

    m.section_break('file system paths', block='paths')
    m.var('output', conf.paths.output, block='paths')
    m.var('public-output', conf.paths.public, block='paths')
    m.var('branch-output', conf.paths.branch_output, block='paths')
    m.var('rst-include', conf.paths.includes, block='paths')
    m.var('branch-source', conf.paths.branch_source, block='paths')
    m.var('public-branch-output', conf.paths.branch_staging, block='paths')

    generated_makefiles = []

    if 'static' in conf.system.make:
        m.section_break('static makefile includes')

        for mfile in conf.system.make.static:
            if mfile.startswith('/'):
                m.include(mfile[1:], ignore=False)
            else:
                m.include(os.path.join(os.path.abspath(os.path.join(__file__, '../../makefiles')), mfile))

    m.newline()

    m.section_break('generated makefiles')

    for target in conf.system.make.generated:
        fn = os.path.sep.join([conf.paths.output, "makefile." + target])
        cloth = os.path.join(conf.paths.buildsystem, "makecloth", target + '.py')

        generated_makefiles.append(fn)

        if target != 'meta':
            m.raw(['-include ' + conf.paths.output + '/makefile.' + target])

        m.target(target=fn, dependency=cloth, block='makefiles')
        m.job(' '.join([conf.system.python, cloth, fn]))
        m.newline()

    m.newline()

    m.target('.PHONY',  generated_makefiles)

    return m

def main():
    conf = get_conf()
    m = generate_meta(conf)

    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" to seed build metadata.')

if __name__ == '__main__':
    main()
