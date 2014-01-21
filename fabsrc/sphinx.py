import itertools
import os.path

from fabric.api import task

import fabfile.process as process
import fabfile.generate as generate
from fabfile.make import runner

from utils.sphinx.prepare import build_prerequisites
from utils.sphinx.workers import sphinx_build, build_worker_wrapper
from utils.sphinx.archives import man_tarball, html_tarball
from utils.sphinx.sites import finalize_single_html_jobs, finalize_dirhtml_build

from fabfile.intersphinx import intersphinx
from fabfile.utils.config import lazy_conf, BuildConfiguration

intersphinx = task(intersphinx)

@task
def target(*targets):
    "Builds a sphinx target with prerequisites and post-processing."

    conf = lazy_conf()

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    sphinx_build(targets, conf, sconf, finalize_build)

#################### Public Fabric Tasks ####################

## modifiers

@task
def prereq():
    "Omnibus operation that builds all prerequisites for a Sphinx build."

    conf = lazy_conf()

    build_prerequisites(conf)

@task
def build(builder='html'):
    "Build a single sphinx target. Does not build prerequisites."

    conf = lazy_conf()

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    build_worker_wrapper(builder, sconf, conf, finalize_build)

############################## Build Finalizing ##############################

# This is temporary. Eventually we want to construct the post-processing jobs
# dynamically and have all of the content processing code in its own module, but
# we're not there yet so this will remain here.

def printer(string):
    print(string)

def finalize_build(builder, sconf, conf):
    if 'language' in sconf:
        # reinitialize conf and builders for internationalization
        conf.paths = render_paths(conf, sconf.language)
        builder = sconf.builder
        target = builder
    else:
        # mms compatibility
        target = builder
        builder = builder.split('-', 1)[0]

    jobs = {
        'linkcheck': [
            { 'job': printer,
              'args': ['[{0}]: See {1}/{0}/output.txt for output.'.format(builder, conf.paths.branch_output)]
            }
        ],
        'dirhtml': [
            { 'job': finalize_dirhtml_build,
              'args': [target, conf]
            }
        ],
        'json': process.json_output_jobs(conf),
        'singlehtml': finalize_single_html_jobs(target, conf),
        'latex': [
            { 'job': process.pdf_worker,
              'args': [target, conf]
            }
        ],
        'man': itertools.chain(process.manpage_url_jobs(conf), [
            { 'job': man_tarball,
              'args': [conf]
            }
        ]),
        'html': [
            { 'job': html_tarball,
              'args': [target, conf]
            }
        ],
        'gettext': process.gettext_jobs(conf),
        'all': [ ]
    }

    if builder not in jobs:
        jobs[builder] = []

    if conf.system.branched is True and conf.git.branches.current == 'master':
        jobs['all'].append(
            { 'job': generate.create_manual_symlink,
              'args': [conf]
            }
        )

    print('[sphinx] [post] [{0}]: running post-processing steps.'.format(builder))
    res = runner(itertools.chain(jobs[builder], jobs['all']), pool=1)
    print('[sphinx] [post] [{0}]: completed {1} post-processing steps'.format(builder, len(res)))
