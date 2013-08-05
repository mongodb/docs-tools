from fabric.api import cd, local, task, env, hide, settings
from fabric.utils import puts
from multiprocessing import cpu_count
import os.path
import pkg_resources
import docs_meta
import datetime

paths = docs_meta.render_paths(True)

from intersphinx import intersphinx
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

def get_sphinx_args(nitpick=None):
    o = ''

    if pkg_resources.get_distribution("sphinx").version.startswith('1.2b1-xgen'):
         o += '-j ' + str(cpu_count()) + ' '

    if nitpick is not None:
        o += '-n -w {0}/build.{1}.log'.format(paths['branch-output'], timestamp('filename'))

    return o

env._clean_sphinx = False

@task
def clean():
    env._clean_sphinx = True

@task
def build(builder='html', tag=None, root=None, nitpick=None):
    if root is None:
        root = paths['branch-output']

    with settings(hide('running'), host_string='sphinx'):
        if env._clean_sphinx is True:
            local('rm -rf {0} {1}'.format(os.path.join(root, 'doctrees' + '-' + builder),
                                          os.path.join(root, builder)))
        else:
            local('mkdir -p {0}/{1}'.format(root, builder))
            puts('[{0}]: created {1}/{2}'.format(builder, root, builder))
            puts('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

            # cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees-{0} -c ./ {3} {2}/source {2}/{0}'
            cmd = 'sphinx-build -b {0} {1} -q -d {2}/doctrees -c ./ {3} {2}/source {2}/{0}'

            if builder.startswith('epub'):
                cmd += ' 2>&1 1>&3 | grep -v "WARNING: unknown mimetype" | grep -v "WARNING: search index" 1>&2; 3>&1'

            local(cmd.format(builder, get_tags(builder, tag), root, get_sphinx_args(nitpick)))

            if builder.startswith('linkcheck'):
                puts('[{0}]: See {1}/{0}/output.txt for output.'.format(builder, root))

            puts('[build]: completed {0} build at {1}'.format(builder, timestamp()))

            if builder.startswith('dirhtml'):
                from process import error_pages
                error_pages()
