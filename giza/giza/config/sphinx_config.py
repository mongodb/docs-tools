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

import sphinx.builders

from giza.strings import hyph_concat
from giza.config.base import RecursiveConfigurationBase
from giza.serialization import ingest_yaml_doc
from giza.config.base import ConfigurationBase

logger = logging.getLogger('giza.config.sphinx_config')

#################### Ingestion and Rendering ####################

def is_legacy_sconf(conf):
    if 'v' not in conf or conf['v'] == 0:
        return True
    else:
        return False

def get_sconf_base(conf):
    sconf_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, 'sphinx.yaml')

    return ingest_yaml_doc(sconf_path)

def render_sconf(edition, builder, language, conf):
    sconf_base = get_sconf_base(conf)

    sconf = SphinxConfig(conf, sconf_base)
    sconf.register(builder, language, edition)

    return sconf

#################### New-Style Config Object ####################

class SphinxConfig(RecursiveConfigurationBase):
    _option_registry = [ 'edition', 'language', 'languages' ]

    def __init__(self, conf, input_obj=None):
        # register the global config, but use our ingestion
        # super(SphinxConfig, self).__init__(None, conf)

        self._conf = None
        self._state = {}
        self._raw = {}
        self.conf = conf
        self.ingest(input_obj)

    def ingest(self, input_obj=None):
        if input_obj is None:
            input_obj = get_sconf_base(self.conf)

        if is_legacy_sconf(input_obj):
            self._raw = render_sphinx_config(input_obj)
        else:
            self._raw = input_obj

    def register(self, builder, language, edition):
        self.language = language
        self.builder = builder
        self.edition = edition

        if edition is None:
            lookup = self.builder
        else:
            lookup = hyph_concat(self.builder, self.edition)

        base = self._raw[lookup]

        for i in ['excluded_files', 'tags', 'languages']:
            if i in base:
                setattr(self, i, base[i])

        m = 'registered language, builder, and edition options: ({0}, {1}, {2})'
        logger.debug(m.format(language, builder, edition))

    @property
    def build_output(self):
        if 'edition' in conf.project and conf.project.edition != conf.project.name:
            dirname = hyph_concat(builder, edition)
        else:
            dirname = builder

        path = os.path.join(conf.paths.projectroot, conf.paths.branch_output, dirname)

        if build_output not in self.state:
            self.state['build_output'] = path

        return path

    @property
    def builder(self):
        return self.state['builder']

    @property
    def excluded_files(self):
        if 'excluded_files' not in self.state:
            return []
        else:
            return self.state['excluded_files']

    @property
    def tags(self):
        return self.state['tags']

    @property
    def langauges(self):
        return self.state['langauges']

    @builder.setter
    def builder(self, value):
        if value in sphinx.builders.BUILTIN_BUILDERS:
            self.state['builder'] = value
        else:
            raise Exception('{0} is not a valid sphinx builder'.format(value))

    @excluded_files.setter
    def excluded_files(self, value):
        if not isinstance(value, list):
            logger.error('excluded_files must be a list.')
            raise TypeError
        else:
            self.state['excluded_files'] = value

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            logger.error('builder tags must be a list.')
            raise TypeError
        else:
            self.state['tags'] = value

    @langauges.setter
    def langauges(self, value):
        if not isinstance(value, list):
            logger.error('langauges must be a list.')
            raise TypeError
        else:
            self.state['langauges'] = value


#################### Rendering for Legacy Config ####################

from copy import deepcopy

def resolve_legacy_sphinx_config(sconf_base, edition, builder, language):
    sconf_base = render_sphinx_config(sconf_base)

    if edition is not None:
        builder = '-'.join([builder, edition])

    sconf = sconf_base[builder]

    sconf['edition'] = edition
    if 'builder' not in sconf:
        sconf['builder'] = builder

    if language is not None:
        sconf['language'] = language

    return sconf

def render_sphinx_config(conf):
    computed = {}

    def resolver(v, conf, computed):
        while 'inherit' in v:
            if v['inherit'] in computed:
                base = deepcopy(computed[v['inherit']])
            else:
                base = deepcopy(conf[v['inherit']])

            del v['inherit']
            base.update(v)
            v = base

        return v

    to_compute = []

    for k,v in conf.items():
        v = resolver(v, conf, computed)
        computed[k] = v

        if 'languages' in v:
            to_compute.append((k,v))

    for k, v in to_compute:
        if k in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in k:
            continue

        if 'languages' in v:
            for lang in v['languages']:
                computed['-'.join([k,lang])] = resolver({ 'inherit': k,
                                                          'language': lang },
                                                        conf, computed)

    for i in computed.keys():
        if i in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in i:
            del computed[i]

    return computed
