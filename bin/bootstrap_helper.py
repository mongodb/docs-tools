import os 
from utils import symlink
from docs_meta import output_yaml
reset_ref = 'HEAD~4'

def init_fabric(buildsystem, conf_file):
    if os.path.isdir('fabfile'):
        os.remove('fabfile')

    symlink('fabfile', os.path.join(buildsystem, 'fabfile'))

    symlink('fabfile', os.path.join(buildsystem, 'fabfile'))

    symlink(name=os.path.join(buildsystem, 'bin', 'docs_meta.yaml'),
            target=os.path.join(os.getcwd(), conf_file))

    symlink(name=os.path.join(buildsystem, 'fabfile', 'utils.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'utils.py'))

    symlink(name=os.path.join(buildsystem, 'fabfile', 'docs_meta.py'),
            target=os.path.join(os.path.abspath(buildsystem), 'bin', 'docs_meta.py'))

def clean_buildsystem(buildsystem, output_dir):
    if os.path.islink('fabfile'):
        os.remove('fabfile')
        print('[bootstrap-clean]: removed fabfile symlink')
            
    import glob
    for i in glob.glob(os.path.join(output_dir, 'makefile.*')):
        os.remove(i)
        print('[bootstrap-clean]: cleaned %s' % i)

    if os.path.exists(buildsystem):
        import shutil
        shutil.rmtree(buildsystem)
        print('[bootstrap-clean]: purged %s' % buildsystem)

def bootstrap():
    """
    The bootstrap file calls this function. Use this as a site for future
    extension.
    """
    output_yaml('meta.yaml')
    print('[bootstrap]: initialized fabfiles and dependencies. Regenerate buildsystem now.')

def main():
    bootstrap()

if __name__ == '__main__':
    main()
