import os.path

from utils.shell import command
from utils.errors import InvalidFile

def transfer_source(sconf, conf):
    target = '-'.join([os.path.join(conf.paths.projectroot, conf.paths.branch_source), sconf.builder])

    if not os.path.exists(target):
        os.makedirs(target)
        print('[sphinx-prep]: created ' + target)
    elif not os.path.isdir(target):
        raise InvalidFile('[sphinx-prep]: {0} exists and is not a directory'.format(target))

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)

    command('rsync --checksum --recursive --delete {0}/ {1}'.format(source_dir, target))
    print('[sphinx-prep]: updated source in {0}'.format(target))
