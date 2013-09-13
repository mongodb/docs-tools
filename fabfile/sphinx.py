from fabric.api import cd, local, task, env, hide, settings
from fabric.utils import puts
from multiprocessing import cpu_count

import itertools
import os
import pkg_resources
import datetime

from utils import ingest_yaml, expand_tree
from clean import cleaner
import generate
import process
import docs_meta

conf = docs_meta.get_conf()
paths = conf.build.paths

from intersphinx import intersphinx, intersphinx_jobs
intersphinx = task(intersphinx)

env.EDITION = None
@task
def edition(val=None):
    if 'editions' in conf.project and val in conf.project.editions:
        env.EDITION = val
        conf.project.edition = val

    if conf.project.name == 'mms':
        conf.build.paths.public_site_output = conf.build.paths.mms[val]

        if val == 'saas':
            conf.build.paths.branch_staging = os.path.join(conf.build.paths.output, val)
        elif val == 'hosted':
            conf.build.paths.branch_staging = os.path.join(conf.build.paths.output, val,
                                                           conf.git.branches.current)

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

def get_sphinx_args(tag):
    o = ''

    if pkg_resources.get_distribution("sphinx").version.startswith('1.2b1-xgen') and (tag is None or not tag.startswith('hosted') or not tag.startswith('saas')):
         o += '-j ' + str(cpu_count()) + ' '

    if env._sphinx_nitpick is True:
        o += '-n -w {0}/build.{1}.log'.format(conf.build.paths.branch_output, timestamp('filename'))

    return o

#################### Associated Sphinx Artifacts ####################

@task
def html_tarball():
    process.copy_if_needed(os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.includes, 'hash.rst'),
                           os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.branch_output,
                                        'html', 'release.txt'))

    basename = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.public_site_output,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    generate.tarball(name=tarball_name,
                     path='html',
                     cdir=os.path.join(conf.build.paths.projectroot,
                                       conf.build.paths.branch_output),
                     sourcep='html',
                     newp=os.path.basename(basename))

    process._create_link(input_fn=os.path.basename(tarball_name),
                         output_fn=os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.public_site_output,
                                                conf.project.name + '.tar.gz'))

@task
def man_tarball():
    basename = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.branch_output,
                            'manpages-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'
    generate.tarball(name=tarball_name,
                     path='man',
                     cdir=os.path.dirname(basename),
                     sourcep='man',
                     newp=conf.project.name + '-manpages'
                     )

    process.copy_if_needed(tarball_name,
                           os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.public_site_output,
                                        os.path.basename(tarball_name)))

    process._create_link(input_fn=os.path.basename(tarball_name),
                         output_fn=os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.public_site_output,
                                                'manpages' + '.tar.gz'))

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
    jobs = itertools.chain(process.manpage_jobs(),
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
        root = conf.build.paths.branch_output

    if nitpick is True:
        nitpick()

    with settings(hide('running'), host_string='sphinx'):
        if env._clean_sphinx is True:
            cleaner([ os.path.join(root, 'doctrees' + '-' + builder),
                      os.path.join(root, builder) ] )
            puts('[clean-{0}]: removed all files supporting the {0} build'.format(builder))
        else:
            dirpath = os.path.join(root, builder)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
                puts('[{0}]: created {1}/{2}'.format(builder, root, builder))

            puts('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

            cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees-{0} -c ./ {3} {2}/source {2}/{0}' # per-builder-doctree
            # cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees -c ./ {3} {2}/source {2}/{0}' # shared doctrees

            if builder.startswith('epub'):
                cmd += ' 2>&1 1>&3 | grep -v "WARNING: unknown mimetype" | grep -v "WARNING: search index" 1>&2; 3>&1'

            local(cmd.format(builder, get_tags(builder, tag), root, get_sphinx_args(tag)))

            puts('[build]: completed {0} build at {1}'.format(builder, timestamp()))

            if builder.startswith('linkcheck'):
                puts('[{0}]: See {1}/{0}/output.txt for output.'.format(builder, root))
            elif builder.startswith('dirhtml'):
                process.error_pages()
            elif builder.startswith('json'):
                process.json_output(conf)
            elif builder.startswith('latex'):
                process.pdfs()
            elif builder.startswith('man'):
                generate.runner( process.manpage_url_jobs() )
                man_tarball()
            elif builder.startswith('html'):
                html_tarball()
