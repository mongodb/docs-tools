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
import stats
import includes
import generate
import sphinx
import tx
import transform

from make import make, force, serial, pool
from deploy import deploy

import fabric
fabric.state.output.status = False
fabric.state.output.aborts = True
fabric.state.output.warnings = True
fabric.state.output.running = False
fabric.state.output.user = True

from fabric.api import task

import primer
