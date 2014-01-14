#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from docs_meta import get_manual_path, get_conf, render_paths

from makecloth import MakefileCloth

from utils.git import get_branch, get_commit

def generate_meta(conf):
    m = MakefileCloth()

    m.section_break('branch/release meta', block='rel')
    m.var('manual-branch', conf.git.branches.manual, block='rel')
    m.var('current-branch', str(get_branch()), block='rel')
    m.var('last-commit', str(get_commit()), block='rel')
    m.var('current-if-not-manual', conf.git.branches.manual, block='rel')

    m.section_break('file system paths', block='paths')
    m.var('output', conf.build.paths.output, block='paths')
    m.var('public-output', conf.build.paths.public, block='paths')
    m.var('branch-output', conf.build.paths['branch-output'], block='paths')
    m.var('rst-include', conf.build.paths.includes, block='paths')
    m.var('branch-source', conf.build.paths['branch-source'], block='paths')
    m.var('public-branch-output', conf.build.paths['branch-staging'], block='paths')

    generated_makefiles = []

    if 'static' in conf.build.system:
        m.section_break('static makefile includes')

        for mfile in conf.build.system.static:
            if mfile.startswith('/'):
                m.include(mfile[1:], ignore=False)
            else:
                m.include(os.path.join(os.path.abspath(os.path.join(__file__, '../../makefiles')), mfile))

    m.newline()

    m.section_break('generated makefiles')

    for target in conf.build.system.files:
        fn = os.path.sep.join([conf.build.paths.output, "makefile." + target])
        cloth = os.path.join(conf.build.paths.buildsystem, "makecloth", target + '.py')

        generated_makefiles.append(fn)

        if target != 'meta':
            m.raw(['-include ' + conf.build.paths.output + '/makefile.' + target])

        m.target(target=fn, dependency=cloth, block='makefiles')
        m.job(' '.join([conf.build.system.python, cloth, fn]))
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
