from fabric.api import cd, local, task, env, hide, settings
from fabric.utils import puts
from multiprocessing import cpu_count

import itertools
import os.path
import pkg_resources
import datetime

from utils import ingest_yaml
from shim import manpage_jobs
import generate
import process
import docs_meta

conf = docs_meta.get_conf()

paths = conf.build.paths

from intersphinx import intersphinx, intersphinx_jobs
intersphinx = task(intersphinx)

def get_tags(target, argtag):
    if argtag is None:
        ret = []
    else:
        ret = [argtag]

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.append('website')
    else:
        ret.append('print')

    return ' '.join([ '-t ' + i for i in ret ])

def timestamp(form='filename'):
    if form == 'filename':
        return datetime.datetime.now().strftime("%Y-%m-%d.%H-%M")
    else:
        return datetime.datetime.now().strftime("%Y-%m-%d, %H:%M %p")

def get_sphinx_args():
    o = ''

    if pkg_resources.get_distribution("sphinx").version.startswith('1.2b1-xgen'):
         o += '-j ' + str(cpu_count()) + ' '

    if env._sphinx_nitpick is True:
        o += '-n -w {0}/build.{1}.log'.format(paths['branch-output'], timestamp('filename'))

    return o

#################### Public Fabric Tasks ####################

## modifiers

env._sphinx_nitpick = False

@task
def nitpick():
    env._sphinx_nitpick = True

env._clean_sphinx = False

@task
def clean():
    env._clean_sphinx = True

## public tasks

@task
def prereq():
    jobs = itertools.chain(manpage_jobs(),
                           generate.table_jobs(),
                           generate.api_jobs(),
                           generate.toc_jobs(),
                           generate.release_jobs(),
                           intersphinx_jobs(),
                           generate.image_jobs())

    job_count = generate.runner(jobs)
    dep_count = generate.runner(process.composite_jobs())
    puts('[sphinx-prep]: built {0} pieces of content'.format(job_count))
    puts('[sphinx-prep]: checked timestamps of all {0} files'.format(dep_count))
    generate.buildinfo_hash()
    generate.source()
    puts('[sphinx-prep]: build environment prepared for sphinx.')

@task
def build(builder='html', tag=None, root=None, nitpick=False):
    if root is None:
        root = paths['branch-output']

    if nitpick is True:
        nitpick()

    with settings(hide('running'), host_string='sphinx'):
        if env._clean_sphinx is True:
            local('rm -rf {0} {1}'.format(os.path.join(root, 'doctrees' + '-' + builder),
                                          os.path.join(root, builder)))
            puts('[clean-{0}]: removed all files supporting the {0} build'.format(builder))
        else:
            local('mkdir -p {0}/{1}'.format(root, builder))
            puts('[{0}]: created {1}/{2}'.format(builder, root, builder))
            puts('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

            cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees-{0} -c ./ {3} {2}/source {2}/{0}' # per-builder-doctree
            # cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees -c ./ {3} {2}/source {2}/{0}' # shared doctrees

            if builder.startswith('epub'):
                cmd += ' 2>&1 1>&3 | grep -v "WARNING: unknown mimetype" | grep -v "WARNING: search index" 1>&2; 3>&1'

            local(cmd.format(builder, get_tags(builder, tag), root, get_sphinx_args()))

            if builder.startswith('linkcheck'):
                puts('[{0}]: See {1}/{0}/output.txt for output.'.format(builder, root))

            puts('[build]: completed {0} build at {1}'.format(builder, timestamp()))

            if builder.startswith('dirhtml'):
                process.error_pages()
            elif builder.startswith('json') and not conf.project.name == 'mms':
                process.json_output()
            elif builder.startswith('latex'):
                process.pdfs()
