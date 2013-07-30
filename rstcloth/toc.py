#!/usr/bin/python2

import os.path
import yaml
import textwrap
import argparse
import table as tb
from rstcloth import RstCloth, fill

class CustomTocTree(object):
    def __init__(self, filename, sort=False):
        self.spec = self._process_spec(filename, sort)

        self.table = None
        self.contents = None
        self.dfn = None

        self.final = False

    def build_table(self):
        self.table = tb.TableData()
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
                #print datum
                if datum['description'] is None:
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
                if self.table is not None:
                    if 'name' in ref:
                        self.table.add_row([ ref['name'], ref['description'] ])
                    else:
                        self.table = None
                if self.contents is not None:
                    self.contents.content(ref['file'], 6, block='toc')
                if self.dfn is not None:
                    if 'name' in ref:
                        text = ref['name']
                    else:
                        text = None
                    
                    link = self.dfn.role('doc', ref['file'], text)

                    idnt = 3
                    if 'level' in ref:
                        idnt = idnt + 3 * ref['level']

                    self.dfn.definition(link, ref['description'], indent=idnt, bold=False, wrap=False)
                    self.dfn.newline()


class AggregatedTocTree(CustomTocTree):
    def __init__(self, filename):
        
        self.table = None
        self.contents = None
        self.dfn = None
        self.final = False

        self.spec = []

        dfn_dir = os.path.abspath(os.path.dirname(filename))

        with open(filename, 'r') as f:
            definition = yaml.safe_load(f)

            filter_specs = {}

            for dfn in definition['files']:
                #print dfn
                if isinstance(dfn, dict):
                    filter_specs[dfn['file']] = dfn['level']
                else:
                    filter_specs[dfn] = 1

        all_objs = {}

        for source in definition['sources']:
            with open(os.path.join(dfn_dir, source), 'r') as f:
                objs = yaml.safe_load_all(f)
                
                for obj in objs:
                    all_objs[obj['file']] = obj

        filter_docs = filter_specs.keys()
        for fn in filter_docs:
            try: 
                self.spec.append(all_objs[fn])
            except KeyError:
                print('[ERROR] [toc]: KeyError "{0}" in file: {1}'.format(fn, filename))
