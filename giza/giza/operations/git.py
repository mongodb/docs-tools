import logging
import os
from tempfile import NamedTemporaryFile

import argh
from sphinx.application import Sphinx, ENV_PICKLE_FILENAME
from sphinx.builders.html import get_stable_hash

from giza.core.app import BuildApp
from giza.core.git import GitRepo
from giza.config.helper import fetch_config
from giza.tools.command import command
from giza.config.sphinx_config import avalible_sphinx_builders

logger = logging.getLogger('giza.operations.git')

@argh.arg('--patch', '-p', nargs='*', dest='git_objects')
@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--signoff', '-s', default=False, action='store_true', dest='git_sign_patch')
@argh.named('am')
@argh.expects_obj
def apply_patch(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch()

    with g.branch(c.runstate.git_branch):
        g.am(patches=c.runstate.git_objects,
             repo='/'.join(['https://github.com', c.git.remote.upstream]),
             sign=c.runstate.git_sign_patch)

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.named('update')
@argh.expects_obj
def pull_rebase(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch()

    with g.branch(c.runstate.git_branch):
        g.update()

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.arg('--commits', '-c', nargs='*', dest='git_objects')
@argh.named('cp')
@argh.expects_obj
def cherry_pick(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    if c.runstate.git_branch is None:
        c.runstate.git_branch = g.current_branch()

    with g.branch(c.runstate.git_branch):
        g.cherry_pick(c.runstate.git_objects)

@argh.arg('--branch', '-b', default=None, dest='git_branch')
@argh.expects_obj
def merge(args):
    c = fetch_config(args)

    g = GitRepo(c.paths.projectroot)

    from_branch = g.current_branch()
    branch_name = str(id(c.runstate.git_branch))

    g.checkout_branch(branch_name, c.runstate.git_branch)

    try:
        g.checkout(branch_name)
        g.rebase(from_branch)
        g.checkout(from_branch)
        g.merge(c.runstate.git_branch)
        logger.info('rebased and merged {0} into {1}'.format(c.runstate.git_branch, from_branch))
    except Exception as e:
        logger.warning('error attempting to merge branch: ' + c.runstate.git_branch)
        logger.error(e)
    finally:
        if g.current_branch != from_branch:
            g.checkout(from_branch)

        g.remove_branch(branch_name, force=True)

@argh.expects_obj
@argh.named("create-branch")
@argh.arg('git_branch')
def create_branch(args):
    conf = fetch_config(args)
    app = BuildApp(conf)
    app.pool = 'process'

    g = GitRepo(conf.paths.projectroot)

    branch = conf.runstate.git_branch
    base_branch = g.current_branch()

    if base_branch == branch:
        base_branch = 'master'
        logger.warning('seeding build data for branch "{0}" from "master"'.format(branch))

    branch_builddir = os.path.join(conf.paths.projectroot,
                                   conf.paths.output, branch)

    base_builddir = os.path.join(conf.paths.projectroot,
                                   conf.paths.output, base_branch)

    if g.branch_exists(branch):
        logger.info('checking out branch "{0}"'.format(branch))
    else:
        logger.info('creating and checking out a branch named "{0}"'.format(branch))

    g.checkout_branch(branch)

    cmd = "rsync -r --times --checksum {0}/ {1}".format(base_builddir, branch_builddir)
    logger.info('seeding build directory for "{0}" from "{1}"'.format(branch, base_branch))
    command(cmd)
    logger.info('branch creation complete.')

    # get a new config here for the new branch
    conf = fetch_config(args)
    for builder in [ b
                     for b in avalible_sphinx_builders()
                     if os.path.isdir(os.path.join(conf.paths.projectroot, conf.paths.branch_output, b)) ]:
        t = app.add('task')
        t.job = fix_build_environment
        t.args = (builder, conf)
        t.target = True
        t.description = "fix up sphinx environment for builder '{0}'".format(builder)

    app.run()


def fix_build_environment(builder, conf):
    fn = os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder, '.buildinfo')
    logger.info('updating cache for: ' + builder)

    if not os.path.isfile(fn):
        return

    doctree_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_output, "doctrees-" + builder)

    sphinx_app = Sphinx(
        srcdir=os.path.join(conf.paths.projectroot, conf.paths.branch_output, "source"),
        confdir=conf.paths.projectroot,
        outdir=os.path.join(conf.paths.projectroot, conf.paths.branch_output, builder),
        doctreedir=doctree_dir,
        buildername=builder,
        status=NamedTemporaryFile(),
        warning=NamedTemporaryFile()
        )

    sphinx_app.env.topickle(os.path.join(doctree_dir, ENV_PICKLE_FILENAME))

    with open(fn, 'r') as f:
        lns = f.readlines()
        tags_hash_ln = None
        for ln in lns:
            if ln.startswith('tags'):
                tags_hash_ln = ln
                break

        if tags_hash_ln == None:
            tags_hash_ln = 'tags: '  + get_stable_hash(sorted(sphinx_app.tags))

    with open(fn, 'w') as f:
        f.write('# Sphinx build info version 1')
        f.write('\n\n')
        f.write('config: ' + get_stable_hash(dict((name, sphinx_app.config[name])
                                                  for (name, desc) in sphinx_app.config.values.items()
                                                  if desc[1] == 'html')))
        f.write('\n')
        f.write(tags_hash_ln)
        f.write('\n')
