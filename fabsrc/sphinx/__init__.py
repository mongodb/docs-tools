import os.path

from fabric.api import task

from fabfile.intersphinx import intersphinx
from fabfile.utils.config import lazy_conf, BuildConfiguration
from fabfile.sphinx.prepare import build_prerequisites
from fabfile.sphinx.workers import sphinx_build, build_worker_wrapper

intersphinx = task(intersphinx)

@task
def target(*targets):
    "Builds a sphinx target with prerequisites and post-processing."

    conf = lazy_conf()

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    sphinx_build(targets, conf, sconf)

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

    build_worker_wrapper(builder, sconf, conf)
