import os
from shutil import rmtree, copyfile

# duplicated to avoid circularly and early dependency problems
def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink(name, target)
        except ImportError:
            exit('ERROR: platform does not contain support for symlinks. Windows users need to pywin32.')

# this function is the old "omnibus" bootstrap and remains for compatibility
# with older bootstrap.py scripts.
def init_fabric(buildsystem, conf_file):
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

    # utils linking
    symlink(name=os.path.join(buildsystem, 'bin', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))
    symlink(name=os.path.join(buildsystem, 'makecloth', 'utils'),
            target=os.path.join(os.path.abspath(buildsystem), 'utils'))
    symlink(name=os.path.join(buildsystem, 'utils', 'docs_meta.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'docs_meta.py'))
