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

import os.path
import logging
import itertools
import copy

import yaml

from giza.config.main import Configuration
from giza.config.error import ConfigurationError
from giza.config.runtime import RuntimeStateConfig
from giza.config.project import get_path_prefix
from giza.config.credentials import CredentialsConfig, get_credentials_skeleton
from giza.config.sphinx_config import render_sconf

from giza.content.release.tasks import register_releases
from giza.content.extract.tasks import register_extracts
from giza.content.options.tasks import register_options
from giza.content.examples.tasks import register_examples
from giza.content.steps.tasks import register_steps
from giza.content.glossary.tasks import register_glossary
from giza.content.tocs.tasks import register_toc
from giza.content.apiargs.tasks import register_apiargs
from giza.content.changelog.tasks import register_changelogs

logger = logging.getLogger('giza.config.helper')


def new_credentials_config(conf_path=None):
    if conf_path is None:
        for fn in [os.path.expanduser("~/.giza-credentials.yaml"),
                   os.path.expanduser("~/.mongodb-jira.yaml")]:
            if os.path.isfile(fn):
                conf_path = fn
                break

    if conf_path is None and not (os.path.isfile(conf_path) or isinstance(conf_path, dict)):
        return None
    else:
        return CredentialsConfig(conf_path)


def fetch_config(args):
    c = Configuration()
    c.ingest(args.conf_path)
    c.runstate = args

    register_content_generators(c)

    return c


def register_content_generators(conf):
    logger.debug("registering content generators with config")
    register_options(conf)
    register_steps(conf)
    register_glossary(conf)
    register_releases(conf)
    register_examples(conf)
    register_extracts(conf)
    register_toc(conf)
    register_apiargs(conf)
    register_changelogs(conf)


def new_skeleton_config(conf=None):
    if conf is None:
        conf = Configuration()
        args = RuntimeStateConfig()
        conf.runstate = args

        try:
            register_content_generators(conf)
        except KeyError:
            logger.warning("trouble registering content generators")

        return conf
    elif isinstance(conf, RuntimeStateConfig):
        return fetch_config(conf)
    else:
        return conf


def setup_credentials(args):
    skel = get_credentials_skeleton()

    dump_skel(skel, args)


def new_config(args=None):
    if args in (None, True, False):
        args = RuntimeStateConfig()

        return fetch_config(args)
    elif isinstance(args, RuntimeStateConfig):
        return fetch_config(args)
    elif isinstance(args, Configuration):
        return args
    else:
        raise ConfigurationError


def dump_skel(skel, args):
    conf_path = os.path.expanduser(os.path.join("~", args.user_conf_path))
    if os.path.exists(conf_path) and args.force is False:
        logger.error('{0} already exists. exiting.'.format(conf_path))
        exit(1)

    with open(conf_path, 'w') as f:
        yaml.dump(skel, f, default_flow_style=False)
        f.write('...\n')
        logger.info('wrote scrumpy configuration skeleton to: {0}')


def get_builder_jobs(conf):
    # assemble a list to generate tasks in the form of:
    # ((edition, language, builder), (conf, sconf))

    for edition, language, builder in itertools.product(conf.runstate.editions_to_build,
                                                        conf.runstate.languages_to_build,
                                                        conf.runstate.builder):
        yield ((edition, language, builder),
               get_sphinx_build_configuration(edition, language, builder, conf.runstate))


def get_restricted_builder_jobs(conf):
    build_source_copies = set()

    for ((edition, langauge, builder), (bconf, sconf)) in get_builder_jobs(conf):
        if bconf.paths.branch_source not in build_source_copies:
            build_source_copies.add(bconf.paths.branch_source)

            yield ((edition, langauge, builder), (bconf, sconf))


def get_sphinx_build_configuration(edition, language, builder, args):
    """
    Given an ``edition``, ``language`` and ``builder`` strings and the runtime
    arguments, return copies of the configuration (``conf``) and sphinx
    configuration (``sconf``) objects.
    """
    args._conf = None
    args = copy.deepcopy(args)

    args.language = language
    args.edition = edition
    args.builder = builder

    conf = fetch_config(args)
    args.conf = conf
    sconf = render_sconf(edition, builder, language, conf)

    return conf, sconf


def get_manual_path(conf):
    if conf.system.branched is False:
        return conf.project.tag
    else:
        branch = conf.git.branches.current
        return get_path_prefix(conf, branch)


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
        v['path'] = get_path_prefix(conf, branch)

        v['text'] = version
        if version == conf.version.stable:
            v['text'] += ' (current)'

        if version == conf.version.upcoming:
            v['text'] += ' (upcoming)'

        v['current'] = True if idx == current_version_index else False

        o.append(v)

    return o
