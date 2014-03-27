import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from utils.shell import command
from utils.errors import InvalidFile

def transfer_source(sconf, conf):
    target = os.path.join(conf.paths.projectroot, conf.paths.branch_source)

    if not os.path.exists(target):
        os.makedirs(target)
        logger.debug('created directory for sphinx build: {0}'.format(target))
    elif not os.path.isdir(target):
        msg = '"{0}" exists and is not a directory'.format(target)
        logger.error(msg)
        raise InvalidFile(msg)

    source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)

    command('rsync --checksum --recursive --delete {0}/ {1}'.format(source_dir, target))
    logger.info('prepared source for sphinx build in {0}'.format(target))
