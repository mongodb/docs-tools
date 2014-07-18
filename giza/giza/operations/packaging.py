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
import datetime
import os
import tarfile

logger = logging.getLogger('giza.operations.packaging')

try:
    import cPickle as pickle
except ImportError:
    import pickle

import argh

from giza.config.helper import fetch_config
from giza.serialization import dict_from_list

def package_filename(archive_path, target, conf):
    fn = [ conf.project.name ]

    if target is not None:
        tag = ''.join([ i if i not in ['push', 'stage'] else '' for i in target.split('-') ])
        if tag != '':
            fn.append(tag)

    fn.extend([ conf.git.branches.current,
                datetime.datetime.utcnow().strftime('%s'),
                conf.git.commit[:8] ])

    fn = os.path.join(archive_path, '-'.join(fn) + '.tar.gz')

    return fn

@argh.named('create')
def create_pacakge(args):
    target = 'push'
    conf = fetch_config(args)
    pconf = dict_from_list(conf.system.files.data.push)[target]

    # make sure the object is fully resolved before we put it into storage
    dynamics = [conf.deploy]
    for key in conf.system.files.data.keys():
        getattr(conf.system.files.data, key)

    conf_dump_path = os.path.join(conf.paths.projectroot,
                                  conf.paths.branch_output,
                                  'conf-dump-{0}.pickle'.format(conf.git.commit))
    with open(conf_dump_path, 'w') as f:
        pickle.dump(conf, f)

    arc_path = os.path.join(conf.paths.projectroot, conf.paths.buildarchive)
    arc_fn = package_filename(arc_path, target, conf)
    if not os.path.exists(arc_path):
        os.makedirs(arc_path)

    input_path = os.path.join(conf.paths.projectroot,
                              conf.paths.output,
                              pconf['paths']['local'])
    output_path_name = conf.git.branches.current

    if conf.project.branched is True:
        input_path = os.path.join(input_path, conf.git.branches.current)
    else:
        output_path_name = os.path.split(pconf['paths']['local'])[-1]

    # ready to write the tarball
    with tarfile.open(arc_fn, 'w:gz') as t:
        t.add(name=input_path,
              arcname=output_path_name)
        t.add(conf_dump_path, arcname=os.path.basename(conf_dump_path))

        if 'static' in pconf['paths']:
            for path in pconf['paths']['static']:
                rendered_path = os.path.join(conf.paths.projectroot,
                                             conf.paths.public, path)
                if os.path.exists(rendered_path):
                    t.add(name=rendered_path,
                          arcname=path)

    logger.info('wrote build package to: {0}'.format(arc_fn))
