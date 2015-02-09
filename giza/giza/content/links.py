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

"""
Creates symbolic links in the build output based on definitions in the
(typically) "build/conf/integration.yaml" file in the ``base.links`` key.
"""

import os.path
import logging

from giza.tools.files import create_link

logger = logging.getLogger('giza.content.links')


def _link_path(path, conf):
    return os.path.join(conf.paths.projectroot,
                        conf.paths.public,
                        path)


def get_top_level_links(links, conf):
    ret = []

    def process_target_list(lst):
        for name, target in lst.items():
            if target == '{{current_branch}}':
                target = conf.git.branches.current

            yield (_link_path(name, conf), target)

    if isinstance(links, list):
        for link in links:
            ret.extend(process_target_list(link))
    else:
        ret.extend(process_target_list(links))

    return ret


def get_public_links(conf):
    iconf = conf.system.files.data.integration

    try:
        return get_top_level_links(iconf['base']['links'], conf)
    except KeyError:
        return []


def create_manual_symlink(conf):
    public_links = get_public_links(conf)

    for name, target in public_links:
        logger.info('creating link to "{0}", named "{1}"'.format(target, name))
        create_link(target, name)
