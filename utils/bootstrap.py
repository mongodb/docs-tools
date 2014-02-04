import os.path
import subprocess

from shutil import rmtree

try:
    from utils.files import symlink
    from utils.config import lazy_conf
except:
    from files import symlink
    from config import lazy_conf

def primer():
    os.remove(os.path.join(os.getcwd(), 'fabfile'))
    main_build = os.path.abspath(os.path.join(os.getcwd(), '..', 'build', 'primer'))
    primer_build = os.path.join(os.getcwd(), 'build')
    primer_conf = os.path.join(os.getcwd(), 'config')

    if not os.path.exists(main_build):
        os.makedirs(main_build)
    elif not os.path.isdir(main_build):
        raise Exception("[ERROR]: {0} is not a directory".format(main_build))

    if not os.path.islink(primer_build):
        rmtree(primer_build)
    else:
        os.remove(primer_build)

    symlink(name='build', target=main_build)

    symlink(name='fabfile',
            target=os.path.abspath(os.path.join(main_build, '..', 'docs-tools', 'fabsrc')))

    symlink(name=os.path.join('build', 'docs-tools'),
            target=os.path.abspath(os.path.join(main_build, '..', 'docs-tools')))

    symlink(name='conf.py',
            target=os.path.abspath(os.path.join(main_build, '..', '..', 'conf.py')))

    symlink(name=os.path.join('source', '.static'),
            target=os.path.abspath(os.path.join(main_build, '..', '..', 'source', '.static')))

    for conf_fn in ['sphinx.yaml']:
        symlink(name=os.path.join(primer_conf, conf_fn),
                target=os.path.abspath(os.path.join(main_build, '..', '..', 'config', conf_fn)))

    print('[bootstrap]: initialized "primer" project.')

def makefile_meta():
    # because this is typically called by bootstrap.py, projectroot is the
    # doctools directory.
    conf = lazy_conf(None)

    # re/generate the makefile.meta

    script_path = os.path.join(conf.paths.projectroot,
                               conf.paths.buildsystem,
                               'makecloth', 'meta.py')
    makefn_path = os.path.join(conf.paths.projectroot,
                               conf.paths.output,
                               'makefile.meta')

    cmd = 'python {0} {1}'.format(script_path, makefn_path).split()
    subprocess.check_call(cmd)

def fabric(buildsystem, conf_file):
    fab_dir = 'fabfile'

    if os.path.islink(fab_dir):
        os.remove(fab_dir)
    elif os.path.isdir(fab_dir):
        rmtree(fab_dir)

    symlink(name='fabfile',
            target=os.path.join(buildsystem, 'fabsrc'))

    symlink(name=os.path.join(buildsystem, 'fabsrc', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))

    symlink(name=os.path.join(buildsystem, 'fabsrc', 'docs_meta.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'docs_meta.py'))

    print('[bootstrap]: initialized fabric/ directory.')


def config(buildsystem, conf_file):
    # config file injection
    meta_link = os.path.join(buildsystem, 'bin', 'docs_meta.yaml')

    if os.path.exists(meta_link):
        os.remove(meta_link)

    symlink(name=meta_link, target=os.path.join(os.getcwd(), conf_file))

    # config directory
    conf_dir_link = os.path.join(buildsystem, 'config')

    if os.path.exists(conf_dir_link):
        os.remove(conf_dir_link)

    symlink(name=conf_dir_link, target=os.path.dirname(conf_file))

    print('[bootstrap]: initialized config/ directory.')

def utils(buildsystem, conf_file):
    # utils linking, the first should be redundant.

    symlink(name=os.path.join(buildsystem, 'bin', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))

    symlink(name=os.path.join(buildsystem, 'makecloth', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))

    symlink(name=os.path.join(buildsystem, 'utils', 'docs_meta.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'docs_meta.py'))

    print('[bootstrap]: initialized utils/ directory.')
