import os.path
import yaml
import textwrap
import argparse

from utils.rstcloth.table import TableData
from utils.rstcloth.rstcloth import RstCloth, fill

from utils.config import lazy_conf

class CustomTocTree(object):
    def __init__(self, filename, conf=None, sort=False):
        self.spec = self._process_spec(filename, sort)

        self.conf = lazy_conf(conf)

        if "ref-toc" in filename:
            self._is_ref = True
        else:
            self._is_ref = False

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
                if 'edition' not in ref:
                    pass
                elif 'edition' in self.conf.project and ref['edition'] != self.conf.project.edition:
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
                    raise Exception('[ERROR] [toc]: KeyError "{0}" in file: {1}'.format(fn, filename))
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
