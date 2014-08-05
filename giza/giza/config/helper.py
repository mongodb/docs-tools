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

import logging

logger = logging.getLogger('giza.config.helper')

from giza.config.main import Configuration
from giza.config.runtime import RuntimeStateConfig

def fetch_config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    return c

def new_config():
    args = RuntimeStateConfig()

    return fetch_config(args)

def dump_skel(skel, args):
    conf_path = os.path.expanduser(os.path.join("~", args.user_conf_path))
    if os.path.exists(conf_path) and args.force is False:
        logger.error('{0} already exists. exiting.'.format(conf_path))
        exit(1)

    with open(conf_path, 'w') as f:
        yaml.dump(skel, f, default_flow_style=False)
        f.write('...')
        logger.info('wrote scrumpy configuration skeleton to: {0}')

def get_path(conf, branch):
    # for backwards compatibility
    return conf.project.sitepath

def get_manual_path(conf):
    if conf.system.branched is False:
        return conf.project.tag
    else:
        branch = conf.git.branches.current
        return get_path(conf, branch)

def get_versions(conf):
    o = []

    current_branch = conf.git.branches.current

    if current_branch not in conf.git.branches.published:
        current_version_index = 0
    else:
        current_version_index = conf.git.branches.published.index(current_branch)

    for idx, version in enumerate(conf.version.published):
        v = {}

        branch = conf.git.branches.published[idx]
        v['path'] = get_path(conf, branch)

        v['text'] = version
        if version == conf.version.stable:
            v['text'] += ' (current)'

        if version == conf.version.upcoming:
            v['text'] += ' (upcoming)'

        v['current'] = True if idx == current_version_index else False

        o.append(v)

    return o
