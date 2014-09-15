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
import os.path

logger = logging.getLogger('giza.content.toc')

import yaml
from giza.tools.files import expand_tree

from rstcloth.rstcloth import RstCloth, fill
from rstcloth.table import TableData, TableBuilder, RstTable

#################### Rendering ####################

class CustomTocTree(object):
    def __init__(self, filename, conf, sort=False):
        if "ref-toc" in filename:
            self._is_ref = True
            sort = True
        else:
            self._is_ref = False

        self.spec = self._process_spec(filename, sort)

        self.conf = conf
        self.table = None
        self.contents = None
        self.dfn = None

        self.final = False

    def build_table(self):
        self.table = TableData()
        self.table.add_header(['Name', 'Description'])

    def build_dfn(self):
        self.dfn = RstCloth()
        self.dfn.directive('class', 'toc')
        self.dfn.newline()

    def build_contents(self):
        self.contents = RstCloth()
        self.contents.directive('class', 'hidden')
        self.contents.newline()
        self.contents.directive('toctree', fields=[('titlesonly', '')], indent=3)
        self.contents.newline()

    def _process_spec(self, spec, sort=False):
        o = []

        with open(spec, 'r') as f:
            data = yaml.safe_load_all(f)

            for datum in data:
                if 'description' not in datum or datum['description'] is None:
                    datum['description'] = ''

                if sort is False:
                    pass
                elif 'name' not in datum:
                    sort = False

                o.append(datum)

        if sort is True:
            o.sort(key=lambda o: o['name'])

        return o

    def finalize(self):
        if not self.final:
            for ref in self.spec:
                if 'edition' in ref:
                    if 'edition' in self.conf.project:
                        if isinstance(ref['edition'], list) and self.conf.project.edition not in ref['edition']:
                            continue
                        elif ref['edition'] != self.conf.project.edition:
                            continue

                if self.table is not None:
                    if 'text' in ref:
                        if ref['name'] is None:
                            self.table.add_row( [ '', ref['text'] ] )
                        else:
                            self.table.add_row( [ ref['name'], ref['text'] ])
                    if 'name' in ref:
                        self.table.add_row([ ref['name'], ref['description'] ])
                    else:
                        self.table = None

                if self.contents is not None and 'file' in ref:
                    if 'name' in ref and self._is_ref is False:
                        self.contents.content("{0} <{1}>".format(ref['name'], ref['file']), 6, wrap=False, block='toc')
                    else:
                        self.contents.content(ref['file'], 6, wrap=False, block='toc')

                if self.dfn is not None:
                    if 'name' in ref:
                        text = ref['name']
                    else:
                        text = None

                    if 'level' in ref:
                        idnt = 3 * ref['level']
                    else:
                        idnt = 3

                    if 'class' in ref:
                        self.dfn.directive(name='class', arg=ref['class'], indent=idnt)
                        idnt += 3

                    if 'text' in ref:
                        if ref['name'] is None:
                            self.dfn.content(ref['text'], idnt)
                        else:
                            self.dfn.definition(ref['name'], ref['text'], indent=idnt, bold=False, wrap=False)
                    else:
                        link = self.dfn.role('doc', ref['file'], text)
                        self.dfn.definition(link, ref['description'], indent=idnt, bold=False, wrap=False)

                    self.dfn.newline()

class TocError(Exception): pass

class AggregatedTocTree(CustomTocTree):
    def __init__(self, filename, conf):
        self.conf = conf

        self.table = None
        self.contents = None
        self.dfn = None
        self.final = False

        self.spec = []

        dfn_dir = os.path.abspath(os.path.dirname(filename))

        with open(filename, 'r') as f:
            definition = yaml.safe_load(f)

            filter_specs = []

            for dfn in definition['files']:
                if isinstance(dfn, dict):
                    if 'edition' in dfn:
                        if dfn['edition'] != self.conf.project.edition:
                            continue

                    if 'file' in dfn:
                        filter_specs.append( (dfn['file'],  dfn['level'], True) )
                    elif 'text' in dfn:
                        if 'title' in dfn:
                            filter_specs.append( ( (dfn['title'], dfn['text']), dfn['level'], False ) )
                        else:
                            filter_specs.append( ( dfn['text'], dfn['level'], False ) )
                    else:
                        raise Exception('[ERROR] [toc]: problem with {0} in {0}'.format(dfn, filename))
                else:
                    filter_specs.append( (dfn,  1, True) )

        all_objs = {}

        self._first_source = definition['sources'][0]

        for source in definition['sources']:
            with open(os.path.join(dfn_dir, source), 'r') as f:
                objs = yaml.safe_load_all(f)

                for obj in objs:
                    all_objs[obj['file']] = obj

        for fn, level, is_file in filter_specs:
            if is_file is True:
                try:
                    obj = all_objs[fn]
                    obj['level'] = level
                    self.spec.append(obj)
                except KeyError:
                    msg = 'toc: KeyError "{0}" in file: {1}'.format(fn, filename)
                    logger.error(msg)
                    raise TocError(msg)
            else:
                # translation
                if isinstance(fn, tuple):
                    self.spec.append( { 'name': fn[0],
                                        'level': level,
                                        'text': fn[1] } )
                else:
                    self.spec.append( { 'name': None,
                                        'level': level,
                                        'text': fn } )


#################### Table of Contents Generator ####################

### Internal Methods

def _get_toc_output_dir(paths):
    return os.path.join(paths.projectroot, paths.branch_source, 'includes', 'toc')

def _get_toc_base_name(fn):
    bn = os.path.basename(fn)

    if bn.startswith('ref-toc-'):
        return os.path.splitext(bn)[0][8:]
    elif bn.startswith('toc-') or bn.startswith('ref-spec-'):
        return os.path.splitext(bn)[0][4:]

def _get_toc_output_name(name, type, paths):
    dirname = _get_toc_output_dir(paths)

    if type == 'toc':
        return os.path.join(dirname, '{0}.rst'.format(name))
    else:
        return os.path.join(dirname, '{0}-{1}.rst'.format(type, name))

def _generate_toc_tree(fn, fmt, base_name, paths, conf):
    if fmt == 'spec':
        logger.debug('generating spec toc {0}'.format(fn))

        toc = AggregatedTocTree(fn, conf)
        fmt = toc._first_source[0:3]
        toc.build_dfn()
        toc.build_table()
        toc.finalize()

        if fmt == 'ref':
            outfn = _get_toc_output_name(base_name, 'table', paths)
            t = TableBuilder(RstTable(toc.table))
            t.write(outfn)
            logger.debug('wrote spec ref-toc: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            logger.debug('wrote spec toc: '  + outfn)
    else:
        logger.debug('generating toc {0}'.format(fn))

        toc = CustomTocTree(fn, conf)
        toc.build_contents()

        if fmt == 'toc':
            toc.build_dfn()
        elif fmt == 'ref':
            toc.build_table()

        toc.finalize()

        outfn = _get_toc_output_name(base_name, 'toc', paths)
        toc.contents.write(outfn)
        logger.debug('wrote toc: '  + outfn)

        if fmt == 'ref':
            outfn = _get_toc_output_name(base_name, 'table', paths)
            t = TableBuilder(RstTable(toc.table))
            t.write(outfn)
            logger.debug('wrote ref toc: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            logger.debug('wrote toc file: '  + outfn)

def toc_tasks(conf, app):
    paths = conf.paths

    for fn in expand_tree(paths.includes, 'yaml'):
        if not (fn.startswith(os.path.join(paths.includes, 'toc')) or
                fn.startswith(os.path.join(paths.includes, 'ref-toc')) or
                fn.startswith(os.path.join(paths.includes, 'ref-spec'))):
            continue
        elif len(fn) >= 24:
            task = app.add('task')
            base_name = _get_toc_base_name(fn)
            target = []

            fmt = fn[20:24]
            if fmt != 'spec':
                fmt = fn[16:19]

            task.dependency = os.path.join(paths.projectroot, fn)
            task.job = _generate_toc_tree
            task.args = [fn, fmt, base_name, paths, conf]
            task.description = 'generating {0} from {1}'.format(fmt, fn)

            if fmt != 'spec':
                target.append(_get_toc_output_name(base_name, 'toc', paths))

            is_ref_spec = fn.startswith(os.path.join(os.path.dirname(fn), 'ref-spec'))

            if not is_ref_spec and (fmt == 'toc' or fmt == 'spec'):
                target.append(_get_toc_output_name(base_name, 'dfn-list', paths))
            elif fmt == 'ref' or is_ref_spec:
                target.append(_get_toc_output_name(base_name, 'table', paths))

            task.target = target

            logger.debug('added task for generating toc from {0}'.format(fn))

def toc_clean(conf):
    rm_rf(_get_toc_output_dir(conf.paths))
    logger.info('removed all generated toc artifacts.')
