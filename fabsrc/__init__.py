import sys
import os.path
import logging

logger = logging.getLogger() # define root logger
logging.basicConfig(level=logging.INFO) # set basic default log level

import log
import stage
import clean
import git
import process
import tools

try:
    import stats
except ImportError:
    logger.info('optional dependency "Droopy" not installed.')
    pass

import includes
import generate
import sphinx
import tx
import transform

from make import make, force, serial, pool, parallel
from deploy import deploy

import fabric
fabric.state.output.status = False
fabric.state.output.aborts = True
fabric.state.output.warnings = True
fabric.state.output.running = False
fabric.state.output.user = True

from fabric.api import task

import primer
