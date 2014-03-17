import os.path
import subprocess

from shutil import rmtree

try:
    from utils.files import symlink
    from utils.git import GitRepo
except:
    from files import symlink
    from git import GitRepo

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

def makefile_meta(conf):
    # re/generate the makefile.meta

    script_path = os.path.join(conf.paths.projectroot,
                               conf.paths.buildsystem,
                               'makecloth', 'meta.py')
    makefn_path = os.path.join(conf.paths.projectroot,
                               conf.paths.output,
                               'makefile.meta')

    cmd = 'python {0} {1}'.format(script_path, makefn_path).split()

    try:
        subprocess.check_call(cmd)
    except:
        subprocess.check_call('python {0} {1}'.format(os.path.join('build', 'docs-tools', 'makecloth', 'meta.py'),
                                                      os.path.join('build', 'makefile.meta')))
    finally:
        return

def pin_tools(conf):
    if 'tools' in conf.system:
        if conf.system.tools.pinned is True:
            print('[bootstrap]: tool pinning engaged.')
            if 'ref' not in conf.system.tools or conf.system.tools.ref == 'HEAD':
                print('[bootstrap]: Cannot pin tools to HEAD, '
                      'which is the default for non-pinned projects.')
            else:
                repo = GitRepo(path=conf.paths.buildsystem)

                if repo.sha() == conf.system.tools.ref:
                    print('[bootstrap]: tools already pinned to {0}. '
                          'Continuing without action.'.format(conf.system.tools.ref))
                else:
                    repo.checkout(conf.system.tools.ref)
                    print("[bootstrap]: pinned tools repo to: {0}".format(conf.system.tools.ref))
        else:
            print('[bootstrap]: tool pinning is not enabled.')

    else:
        print('[bootstrap]: tool pinning is not supported by this project.')

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
