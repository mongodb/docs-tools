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
from giza.operations.deploy import deploy_worker

############### Helper ###############

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

#################### Worker Functions ####################

def dump_config(conf):
    # make sure the object is fully resolved before we put it into storage
    dynamics = [conf.deploy]
    for key in conf.system.files.data.keys():
        getattr(conf.system.files.data, key)

    conf_dump_path = os.path.join(conf.paths.projectroot,
                                  conf.paths.branch_output,
                                  'conf.pickle')

    with open(conf_dump_path, 'w') as f:
        pickle.dump(conf, f)

    return conf_dump_path

def create_package(target, conf):
    if target is None:
        pconf = conf.system.files.data.push[0]
        target = pconf['target']
    else:
        pconf = dict_from_list(conf.system.files.data.push)[target]

    logger.info('creating package for target "{0}"'.format(target))

    conf_dump_path = dump_config(conf)

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

def extract_package(conf):
    if conf.runstate.package_path.startswith('http'):
        path = fetch_package(path, conf)
    elif os.path.exists(conf.runstate.package_path):
        path = conf.runstate.package_path
    else:
        m = "package {0} does not exist".format(conf.runstate.package_path)
        logger.critical(m)
        raise GizaPackagingError(m)

    with tarfile.open(path, "r:gz") as t:
        t.extractall(os.path.join(conf.paths.projectroot, conf.paths.public))

    conf_extract_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output, 'conf.pickle')

    with open(conf_extract_path, 'rb') as f:
        new_conf = pickle.load(f)

    if os.path.exists(conf_extract_path):
        os.remove(conf_extract_path)

    return new_conf

def fetch_package(path, conf):
    if not path.startswith('http') and os.path.exists(path):
        return path

    local_path = path.split('/')[-1]

    tar_path = os.path.join(conf.paths.projectroot,
                            conf.paths.buildarchive,
                            local_path)

    if not os.path.exists(tar_path):
        with closing(urllib2.urlopen(path)) as u:
            with open(tar_path, 'w') as f:
                f.write(u.read())
        logger.info('downloaded {0}'.format(local_path))
    else:
        logger.info('{0} exists locally, not downloading.'.format(local_path))

    return tar_path

#################### Command Entry Points ####################

@argh.arg('--target', '-t', nargs=1, default=[None], dest='push_targets')
def create(args):
    conf = fetch_config(args)
    target = conf.runstate.push_targets[0]

    create_package(target, conf)

@argh.arg('--path', dest='package_path')
def unwind(args):
    conf = fetch_config(args)

    conf.runstate.package_path = fetch_package(conf.runstate.package_path, conf)
    logger.info('extracting package: ' + conf.runstate.package_path)
    extract_package(conf)
    logger.info('extracted package')

@argh.arg('--path', dest='package_path')
@argh.arg('--target', '-t', nargs=1, dest='push_targets')
@argh.arg('--dry-run', '-d', action='store_true', dest='dry_run')
def deploy(args):
    conf = fetch_config(args)

    conf.runstate.package_path = fetch_package(conf.runstate.package_path, conf)

    logger.info('extracting package: ' + conf.runstate.package_path)
    new_conf = extract_package(conf)
    logger.info('extracted package')

    app = BuildApp(new_conf)

    logger.info('beginning deploy now.')
    deploy_worker(conf, app)

@argh.arg('--path', dest='package_path')
def fetch(args):
    conf = fetch_config(args)

    if conf.runstate.package_path.startswith('http'):
        fetch_package(conf.runstate.pacage_path, conf)
    else:
        logger.error('{0} is not a url'.format(conf.runstate.package_path))
        raise SystemExit
