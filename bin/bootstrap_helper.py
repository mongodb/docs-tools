import os
from shutil import rmtree, copyfile

reset_ref = 'HEAD~40'

def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink(name, target)
        except ImportError:
            exit('ERROR: platform does not contain support for symlinks. Windows users need to pywin32.')

# compatibility with old bootstrap.py scripts
def init_fabric(buildsystem, conf_file):
    import legacy_bootstrap

    print('[bootstrap] [warning]: legacy bootstrap process. update more thoroughly.')
    legacy_bootstrap.init_fabric(buildsystem, conf_file)

def clean_buildsystem(buildsystem, output_dir):
    if os.path.islink('fabfile'):
        os.remove('fabfile')
        print('[bootstrap-clean]: removed fabfile symlink')
    import glob
    for i in glob.glob(os.path.join(output_dir, 'makefile.*')):
        os.remove(i)
        print('[bootstrap-clean]: cleaned %s' % i)

    if os.path.exists(buildsystem):
        rmtree(buildsystem)
        print('[bootstrap-clean]: purged %s' % buildsystem)

def bootstrap(**kwargs):
    """
    The bootstrap file calls this function. Use this as a site for future
    extension.
    """

    try:
        build_tools_path = kwargs['build_tools_path']
        conf_path = kwargs['conf_path']

        symlink(name=os.path.join(build_tools_path, 'bin', 'utils'),
                target=os.path.join(os.path.abspath(build_tools_path), 'utils'))

        import utils.bootstrap

        utils.bootstrap.fabric(build_tools_path, conf_path)
        utils.bootstrap.config(build_tools_path, conf_path)
        utils.bootstrap.utils(build_tools_path, conf_path)

    except KeyError:
        print('[bootstrap] [warning]: your bootstrap.py is probably out of date. '
              'Please update as soon as possible.')

    import utils.bootstrap

    utils.bootstrap.makefile_meta()

    if 'primer' in os.path.split(os.getcwd()):
        utils.bootstrap.primer()

    print('[bootstrap]: initialized fabfiles and dependencies.')

def main():
    bootstrap()

if __name__ == '__main__':
    main()
