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

from flask import Flask
from flask_environments import Environments
from pymongo import MongoClient


app = Flask(__name__)
env = Environments(app)
env.from_yaml(os.path.join(os.path.abspath(os.path.join('..', os.path.dirname(__file__))), '..', 'config.yaml'))

mongodb = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
db = mongodb[app.config['MONGO_DBNAME']]
