import os
from utils import symlink
from docs_meta import output_yaml
from shutil import rmtree, copyfile
import subprocess

reset_ref = 'HEAD~4'

def init_fabric(buildsystem, conf_file):
    fab_dir = 'fabfile'

    if os.path.islink(fab_dir):
        os.remove(fab_dir)
    elif os.path.isdir(fab_dir):
        rmtree(fab_dir)

    symlink('fabfile', os.path.join(buildsystem, 'fabfile'))

    symlink('fabfile', os.path.join(buildsystem, 'fabfile'))

    # symlink(name=os.path.join(buildsystem, 'bin', 'docs_meta.yaml'),
    #         target=os.path.join(os.getcwd(), conf_file))

    symlink(name=os.path.join(buildsystem, 'fabfile', 'utils.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'utils.py'))

    symlink(name=os.path.join(buildsystem, 'fabfile', 'docs_meta.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'docs_meta.py'))

    # copyfile(src=os.path.join(os.path.abspath(buildsystem), 'bin', 'bootstrap.py'),
    #          dst=os.getcwd())

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

def bootstrap():
    """
    The bootstrap file calls this function. Use this as a site for future
    extension.
    """
    print('[bootstrap]: initialized fabfiles and dependencies. Regenerate buildsystem now.')

    # creating stub meta.yaml
    output_yaml('meta.yaml')

    # re/generate the makefile.meta
    makecloth_path = os.path.join(os.path.abspath(__file__).rsplit(os.path.sep, 2)[0], 'makecloth')
    cmd = 'python {0}/meta.py build/makefile.meta'.format(makecloth_path).split()
    subprocess.check_call(cmd)

def main():
    bootstrap()

if __name__ == '__main__':
    main()
