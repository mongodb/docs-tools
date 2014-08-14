# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from pharaoh.app import flask_app
app = flask_app.app
from pharaoh.app import views
from pharaoh.app import filters

from pharaoh.gunicorn_application import StandaloneApplication

PHARAOH_PATH = os.path.abspath(os.path.join('..', os.path.dirname(__file__)))

def runserver(conf, host, port):
    app.debug = app.config['DEBUG']
    app.logger.setLevel(conf.runstate.level)
    options = {
        'bind': '%s:%s' % (host, port),
        'workers': app.config['WORKERS'],
        'logconfig': os.path.join(PHARAOH_PATH, 'app', 'logging.conf'),

    }
    StandaloneApplication(app, options).run()
