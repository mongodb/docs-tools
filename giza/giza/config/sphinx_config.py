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

import copy
import os.path
import logging

import libgiza.config
import sphinx.builders
import yaml

logger = logging.getLogger('giza.config.sphinx_config')

# Ingestion and Rendering


def is_legacy_sconf(conf):
    if 'v' not in conf or conf['v'] == 0:
        return True
    else:
        return False


def get_sconf_base(conf):
    sconf_path = os.path.join(conf.paths.projectroot, conf.paths.builddata, 'sphinx.yaml')
    with open(sconf_path, 'r') as f:
        sconf = yaml.safe_load(f)

    return sconf


def render_sconf(edition, builder, language, conf):
    sconf_base = get_sconf_base(conf)

    sconf = SphinxConfig(conf, sconf_base)
    sconf.register(builder, language, edition)

    return sconf

# Helpers


def resolve_builder_path(builder, edition, language, conf):
    dirname = builder

    if edition is not None and edition != conf.project.name:
        dirname = '-'.join((dirname, edition))

    if language is not None and language != 'en':
        dirname = '-'.join((dirname, language))

    return dirname


def avalible_sphinx_builders():
    builders = sphinx.builders.BUILTIN_BUILDERS.keys()
    builders.append('slides')
    builders.append('publish')

    return builders

# New-Style Config Object


class SphinxConfig(libgiza.config.RecursiveConfigurationBase):
    _option_registry = ['languages']

    def __init__(self, conf, input_obj=None):
        # register the global config, but use our ingestion
        # super(SphinxConfig, self).__init__(None, conf)

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

        lookup_opts = []

        if edition is None:
            lookup_opts.append(self.builder)
        else:
            lookup_opts.append('-'.join((self.builder, self.edition)))

        base = {}
        for opt in lookup_opts:
            if opt in self._raw:
                base = self._raw[opt]
                break

        for i in ['excluded', 'tags', 'languages']:
            if i in base:
                setattr(self, i, base[i])

        m = 'registered language, builder, and edition options: ({0}, {1}, {2})'
        logger.debug(m.format(language, builder, edition))

    @property
    def name(self):
        if 'name' in self.state:
            return self.state['name']
        else:
            return self.builder

    @name.setter
    def name(self, value):
        self.state['name'] = value

    @property
    def build_output(self):
        if 'build_output' not in self.state:
            self.build_output = None

        return self.state['build_output']

    @build_output.setter
    def build_output(self, value):
        if value is None:
            path = resolve_builder_path(self.builder, self.edition, self.language, self.conf)
            self.state['build_output'] = path
        else:
            self.state['build_output'] = path

    @property
    def fq_build_output(self):
        if 'build_output' not in self.state:
            self.build_output = None

        return os.path.join(self.conf.paths.projectroot,
                            self.conf.paths.branch_output,
                            self.build_output)

    @property
    def language(self):
        if 'language' not in self.state:
            return 'en'
        else:
            return self.state['language']

    @language.setter
    def language(self, value):
        self.state['language'] = value

    @property
    def edition(self):
        if 'edition' in self.state:
            return self.state['edition']
        else:
            if ('edition' in self.conf.project and
                    self.conf.project.edition != self.conf.project.name):

                return self.conf.project.edition
            else:
                return ''

    @edition.setter
    def edition(self, value):
        self.state['edition'] = value

    @property
    def builder(self):
        return self.state['builder']

    @property
    def excluded(self):
        if 'excluded' not in self.state:
            return []
        else:
            return self.state['excluded']

    @property
    def tags(self):
        return self.state['tags']

    @property
    def languages(self):
        return self.state['languages']

    @builder.setter
    def builder(self, value):
        if value in avalible_sphinx_builders():
            self.state['builder'] = value
        else:
            raise TypeError('{0} is not a valid sphinx builder'.format(value))

    @excluded.setter
    def excluded(self, value):
        if not isinstance(value, list):
            logger.error('excluded files must be a list.')
            raise TypeError
        else:
            if 'excluded' in self.state:
                self.state['excluded'].extend(value)
            else:
                self.state['excluded'] = value

    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            logger.error('builder tags must be a list.')
            raise TypeError
        else:
            if 'tags' in self.state:
                self.state['tags'].extend(value)
            else:
                self.state['tags'] = value

    @languages.setter
    def languages(self, value):
        if not isinstance(value, list):
            logger.error('languages must be a list.')
            raise TypeError
        else:
            self.state['languages'] = value


# Rendering for Legacy Config


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
                base = copy.deepcopy(computed[v['inherit']])
            else:
                base = copy.deepcopy(conf[v['inherit']])

            if 'excluded' in v and 'excluded' in base:
                if isinstance(v['excluded'], list):
                    base['excluded'].extend(v['excluded'])
                    del v['excluded']

            del v['inherit']
            base.update(v)
            v = base

        return v

    to_compute = []

    for k, v in conf.items():
        v = resolver(v, conf, computed)
        computed[k] = v

        if 'languages' in v:
            to_compute.append((k, v))

    for k, v in to_compute:
        if k in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in k:
            continue

        if 'languages' in v:
            for lang in v['languages']:
                computed['-'.join([k, lang])] = resolver({'inherit': k,
                                                          'language': lang},
                                                         conf, computed)

    for i in computed.keys():
        if i in ['prerequisites', 'generated-source',
                 'sphinx-builders'] or 'base' in i:
            del computed[i]

    return computed
