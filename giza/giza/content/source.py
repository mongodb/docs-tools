import os.path
import logging
from shutil import rmtree

logger = logging.getLogger('giza.content.source')

from giza.command import command
from giza.content.dependencies import dump_file_hashes
from giza.files import InvalidFile

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

    # we don't want rsync to delete directories that hold generated content in
    # the target so we can have more incremental builds.
    exclusions = "--exclude=" + ' --exclude='.join([ os.path.join('includes', 'steps'),
                                                     os.path.join('includes', 'toc') ])

    command('rsync --times --checksum --recursive {2} --delete {0}/ {1}'.format(source_dir, target, exclusions))

    dump_file_hashes(conf)

    logger.info('prepared source for sphinx build in {0}'.format(target))

def source_tasks(conf, app):
    t = app.add('task')
    t.job = transfer_source
    t.args = [conf]
    t.description = 'transferring source to {0}'.format(conf.paths.branch_source)
    logger.info('adding task to migrate source to {0}'.format(conf.paths.branch_source))

def exclusion_tasks(conf, sconf, app):
    for fn in sconf.excluded_files:
        fqfn = os.path.join(conf.paths.projectroot, conf.paths.branch_source, fn[1:])
        if os.path.exists(fqfn):
            if os.path.isdir(fqfn):
                rmtree(fqfn)
            else:
                os.remove(fqfn)
                logger.debug('removed {0}'.format(fqfn))

    logger.info('removed {0} files'.format(len(sconf.excluded_files)))
