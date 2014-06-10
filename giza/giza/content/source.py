import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from giza.tools.shell import command
from giza.tools.errors import InvalidFile

def transfer_source(conf):
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


def source_tasks(conf, app):
    t = app.add('task')
    t.job = transfer_source
    t.args = [conf]
    t.description = 'transferring source to {0}'.format(conf.paths.branch_source)
    logger.info('adding task to migrate source to {0}'.format(conf.paths.branch_source))
