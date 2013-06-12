#!/usr/bin/python

import sys
import os.path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import utils
from docs_meta import get_manual_path, conf, render_paths

from makecloth import MakefileCloth

m = MakefileCloth()
conf.build.paths.update(render_paths('dict'))

def generate_meta():
    m.section_break('branch/release meta', block='rel')
    m.var('manual-branch', conf.git.branches.manual, block='rel')
    m.var('current-branch', str(utils.get_branch()), block='rel')
    m.var('last-commit', str(utils.get_commit()), block='rel')
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
    m.target('.PHONY', 'meta.yaml')
    m.target('meta.yaml', block='metaymal')
    m.job('fab process.output:meta.yaml process.meta', block='metaymal')
    m.msg('[meta]: regenerated "meta.yaml"', block='metaymal')

    m.section_break('generated makefiles')
    for target in conf.build.system.files:
        file ='/'.join([conf.build.paths.output, "makefile." + target])
        cloth = os.path.join(conf.build.paths.buildsystem, "makecloth", target + '.py')

        generated_makefiles.append(file)
        m.raw(['-include ' + conf.build.paths.output + '/makefile.' + target])

        m.target(target=file, dependency=cloth, block='makefiles')
        m.job(' '.join(["$(PYTHONBIN)", cloth, file]))
        m.newline()

    m.newline()

    m.target('.PHONY',  generated_makefiles)

def main():
    generate_meta()

    m.write(sys.argv[1])
    print('[meta-build]: built "' + sys.argv[1] + '" to seed build metadata.')

if __name__ == '__main__':
    main()
