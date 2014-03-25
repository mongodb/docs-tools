import itertools
import os.path

from fabric.api import task

from fabfile.make import runner
from fabfile.process import pdf_worker

from fabfile.utils.contentlib.links import create_manual_symlink

from fabfile.utils.sphinx.prepare import build_prerequisites
from fabfile.utils.sphinx.workers import sphinx_build
from fabfile.utils.sphinx.archives import man_tarball, html_tarball
from fabfile.utils.sphinx.config import get_sconf
from fabfile.utils.sphinx.sites import finalize_epub_build, finalize_single_html_jobs, finalize_dirhtml_build

from fabfile.intersphinx import intersphinx
from fabfile.utils.config import lazy_conf, render_paths
from fabfile.utils.structures import BuildConfiguration

from fabfile.utils.contentlib.gettext import gettext_jobs
from fabfile.utils.contentlib.json_output import json_output_jobs
from fabfile.utils.contentlib.manpage import manpage_url_jobs

intersphinx = task(intersphinx)

@task(aliases=['build'])
def target(*targets):
    "Builds one or more sphinx targets with prerequisites and post-processing."

    conf = lazy_conf()
    sconf = get_sconf(conf)

    sphinx_build(targets, conf, sconf, finalize_build)

#################### Public Fabric Tasks ####################

## modifiers

@task
def prereq():
    "Omnibus operation that builds all prerequisites for a Sphinx build."

    conf = lazy_conf()

    build_prerequisites(conf)

############################## Build Finalizing ##############################

# This is temporary. Eventually we want to construct the post-processing jobs
# dynamically and have all of the content processing code in its own module, but
# we're not there yet so this will remain here.'

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
        'epub': [ { 'job': finalize_epub_build,
                    'args': [conf] }
        ],
        'json': json_output_jobs(conf),
        'singlehtml': finalize_single_html_jobs(target, conf),
        'latex': [
            { 'job': pdf_worker,
              'args': [target, conf]
            }
        ],
        'man': itertools.chain(manpage_url_jobs(conf), [
            { 'job': man_tarball,
              'args': [conf]
            }
        ]),
        'html': [
            { 'job': html_tarball,
              'args': [target, conf]
            }
        ],
        'gettext': gettext_jobs(conf),
        'all': [ ]
    }

    if builder not in jobs:
        jobs[builder] = []

    if conf.system.branched is True and conf.git.branches.current == 'master':
        jobs['dirhtml'].append(
            { 'job': create_manual_symlink,
              'args': [conf]
            }
        )

    print('[sphinx] [post] [{0}]: running post-processing steps.'.format(builder))
    res = runner(itertools.chain(jobs[builder], jobs['all']), pool=1)
    print('[sphinx] [post] [{0}]: completed {1} post-processing steps'.format(builder, len(res)))
