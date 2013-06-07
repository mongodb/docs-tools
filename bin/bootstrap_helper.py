import os 
from utils import symlink

reset_ref = 'HEAD~4'

def init_fabric(buildsystem, conf_file):
    if os.path.isdir('fabfile'):
        os.remove('fabfile')

    symlink('fabfile', os.path.join(buildsystem, 'fabfile'))

    symlink('docs_meta.yaml', conf_file)

    symlink(name=os.path.join(buildsystem, 'fabfile', 'utils.py'),
            target=os.path.join('../', buildsystem, 'bin', 'utils.py'))

    symlink(name=os.path.join(buildsystem, 'fabfile', 'docs_meta.py'),
            target=os.path.join('../', buildsystem, 'bin', 'docs_meta.py'))

def bootstrap():
    """
    The bootstrap file calls this function. Use this as a site for future
    extension.
    """
    print('[bootstrap]: initialized fabfiles and dependencies. Regenerate buildsystem now.')

def main():
    bootstrap()

if __name__ == '__main__':
    main()
