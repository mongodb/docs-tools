import logging
import os.path

from fabric.api import task, env

logger = logging.getLogger(os.path.basename(__file__))

log_levels = {
    'all': logging.NOTSET,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

env.log_file = None

@task
def file(fn):
    "Set a file to write the log. Specify before setting the log level."
    fn_dir = os.path.dirname(fn)
    if len(fn_dir) != 0 and not os.path.exists(fn_dir):
        os.makedirs(fn_dir)

    env.log_file = fn

@task
def set(level):
    "Set the log level. Values may be 'info', 'debug', 'warning', 'error', 'critical'."

    if level in log_levels:
        env.logLevel = level

        rlogger = logging.getLogger()

        rlogger.setLevel(log_levels[level])

        if env.log_file is not None:
            rlogger.handlers[0].stream.close()
            rlogger.removeHandler(rlogger.handlers[0])

            formatter = logging.Formatter(fmt="%(asctime)s %(filename)s %(funcName)s() [%(lineno)d] %(levelname)s: %(message)s")

            file_handler = logging.FileHandler(env.log_file)
            file_handler.setFormatter(formatter)
            rlogger.addHandler(file_handler)

            logger.info('loging to file {0}'.format(env.log_file))

        logger.debug('set logging level to {0}'.format(log_levels[level]))
