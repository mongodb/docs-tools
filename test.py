import logging
import os
import argparse
import shutil

logger = logging.getLogger(os.path.basename(__file__))

from utils.shell import command, CommandError
from utils.git import get_commit
from utils.files import symlink

def setup_logging(args):
    config = dict()

    if args.logfile is not None:
        config['filename'] = args.logfile

    config['level'] = args.level

    logging.basicConfig(**config)
    logger.debug('set level to: {0}'.format(args.level))

def user_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', '-b', default='master')
    parser.add_argument('--repo', '-r', default='git@github.com:mongodb/docs.git')
    parser.add_argument('--project', '-p', default='manual', choices=['manual', 'mms', 'ecosystem'])

    parser.add_argument('--silent', action='store_const', const=logging.NOTSET, dest='level',
                        help='disable all logging output.')
    parser.add_argument('--debug', action='store_const', const=logging.DEBUG, dest='level',
                        help='enable debug logging output.')
    parser.add_argument('--info', action='store_const', const=logging.INFO, dest='level',
                        help='enable most verbose logging output.')
    parser.add_argument('--logfile', action='store', default=None,
                        help='log to file rather than standard output')

    return parser.parse_args()

def main():
    user = user_input()
    setup_logging(user)

    if user.repo == 'git@github.com:mongodb/docs.git' and user.project != 'manual':
        msg = '[test]: project and repo are not correctly matched'
        logger.error(msg)
        exit(1)

    if not os.path.exists('build'):
        os.makedirs('build')
    elif not os.path.isdir('build'):
        logger.warning('build exists but is not a directory. please investigate.')
        os.remove('build')

    root_path = os.path.abspath(os.getcwd())
    build_path = os.path.join('build', user.project)

    if os.path.exists(build_path):
        logger.info('build directory exists. continuing with quasi-incremental build.')
    else:
        logger.info('cloning repository')
        command('git clone {0} {1}'.format(user.repo, build_path))
        logger.info('cloned repository')

    os.chdir(build_path)

    logger.debug('script working directory is now {0}'.format(os.getcwd()))

    if user.branch != 'master':
        try:
            command('git checkout {0}'.format(branch))
        except CommandError:
            command('git checkout -b {0} origin/{0}'.format(branch))
        except CommandError:
            logger.error('branch name {0} does not exist in remote'.format(branch))
            exit(1)

    bootstrapped_tools_path = os.path.join('build', 'docs-tools')

    if not os.path.exists(bootstrapped_tools_path):
        logger.debug("{0} does not exist".format(bootstrapped_tools_path))
        symlink(name=bootstrapped_tools_path, target=root_path)
        logger.debug('created tools symlink')
    elif os.path.islink(bootstrapped_tools_path):
        logger.debug("{0} is a link. continuing.".format(bootstrapped_tools_path))
    elif os.path.isdir(bootstrapped_tools_path) and not os.path.islink(bootstraped_tools_path):
        logger.warning('a tools directory currently exists, removing.')
        shutil.rmtree(bootstrapped_tools_path)
        symlink(name=bootstrapped_tools_path, target=root_path)
        logger.debug('created tools symlink')

    logger.info('bootstrapping.')
    command('python bootstrap.py safe')
    logger.info('moving on to build the publish target.')

    build_task = command('make publish', capture=True, ignore=True)
    logger.info('completed build task, moving to printing output')

    print_build_output(build_task)

    log_and_propogate_task_return(build_task)

def print_build_output(task):
    if len(task.out) > 0:
        print('=' * 72)
        print(">>> build standard output")
        print(task.out)
        print('=' * 72)
        print()
        logger.debug('returned all standard output')
    else:
        logger.info('no build standard output.')

    if len(task.err) > 0:
        print('=' * 72)
        print(">>> build standard error")
        print(task.err)
        print('=' * 72)
        print()
        logger.debug('returned all standard error')
    else:
        logger.info('no build standard error output.')

def log_and_propogate_task_return(task):
    logger.info('task return code is: {0}'.format(task.return_code))

    if task.return_code != 0:
        logger.error('build was not successful.')
    else:
        logger.info('build successful!')

    logger.debug('exiting now...')
    exit(task.return_code)

if __name__ == '__main__':
    main()
