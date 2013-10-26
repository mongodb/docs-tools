import json
import operator
import os.path
import re
import yaml

from itertools import groupby
from multiprocessing import Pool
from pprint import pprint

from fabric.api import task, local, env
from fabric.utils import puts, abort

from droopy.factory import DroopyFactory
from droopy.lang.english import English
from droopy import Droopy, attr, op

from docs_meta import get_conf
from utils import expand_tree, AttributeDict
from make import runner
import stats_data

####### internal functions for rendering reports #######

class Weakness(object):
    cache = AttributeDict({ 'w': None, 'p': None })

    @attr
    def weasel_list(self, d):
        l = []
        for word in d.words:
            if word in stats_data.ww:
                l.append(word)

        w = list(set(l))
        self.cache.w = w
        return w

    @attr
    def weasel_count(self, d):
        if self.cache.w is not None:
            return len(self.cache.w)
        else:
            return len(self.weasel_list(d))

    def passives(self, d):
        p = stats_data.passive_regex.findall(d.text)
        self.cache.p = stats_data.passive_regex.findall(d.text)
        return p

    @attr
    def passive_list(self, d):
        if self.cache.p is None:
            self.passives(d)

        return list(set([ ' '.join(phrase) for phrase in self.cache.p ]))

    @attr
    def passive_count(self, d):
        if self.cache.p is None:
            self.passives(d)

        return len(self.cache.p)

def _render_report(fn):
    with open(os.path.abspath(fn), 'r') as f:
        text = json.load(f)['text']

    base_fn, source = _resolve_input_file(fn)

    droopy = DroopyFactory.create_full_droopy(text, English())
    droopy.add_bundles(Weakness())
    droopy.foggy_word_syllables = 3

    r = {
        'file': fn,
        'source': source,
        'stats': {
            'weasels': {
                'count': droopy.weasel_count,
                'set': droopy.weasel_list
            },
            'passives': {
                'count': droopy.passive_count,
                'set': droopy.passive_list
            },
            'smog-index': droopy.smog,
            'flesch-level': droopy.flesch_grade_level,
            'flesch-ease': droopy.flesch_reading_ease,
            'coleman-liau': droopy.coleman_liau,
            'word-count': droopy.nof_words,
            'sentence-count': droopy.nof_sentences,
            'sentence-len-avg': droopy.nof_words / droopy.nof_sentences,
            'foggy': {
                'factor':droopy.foggy_factor,
                'count':  droopy.nof_foggy_words,
                'threshold':  droopy.foggy_word_syllables,
                },
            }
        }

    if r['stats']['weasels']['count'] == 0:
        r['stats']['weasels'] = r['stats']['weasels']['count']

    if r['stats']['passives']['count'] == 0:
        r['stats']['passives'] = r['stats']['passives']['count']

    return r

## Path and filneame processing

def _fn_output(tag, conf=None):
    if conf is None:
        conf = get_conf()

    fn = ['stats', 'sweep' ]
    if tag is not None:
        fn.append(tag.replace('/', '-'))
    fn.extend([conf.git.branches.current, conf.git.commit[:6]])

    out_fn = '.'.join(['-'.join(fn), 'yaml'])
    return os.path.join(conf.build.paths.output, out_fn)

def _resolve_input_file(fn):
    if fn.startswith('/'):
        fn = fn[1:]
    if fn.startswith('source'):
        fn = fn[7:]

    base_fn = os.path.splitext(fn)[0]
    source = '.'.join([os.path.join('source', base_fn), 'txt'])

    return base_fn, source

## YAML output wrapper

def _output_report_yaml(data):
   return yaml.safe_dump(data, default_flow_style=False, explicit_start=True)

########## user facing operations ##########

def report_jobs(docs, mask):
    for doc in docs:
        if doc.endswith('searchindex.json') or doc.endswith('globalcontext.json'):
            continue
        elif mask is None:
            yield {
                'job': _render_report,
                'args': dict(fn=doc),
                'target': None,
                'dependency': None
            }
        elif doc.startswith(mask):
            yield {
                'job': _render_report,
                'args': [doc],
                'target': None,
                'dependency': None
            }

## Report Generator
def _generate_report(mask, output_file=None, conf=None):
    if conf is None:
        conf = get_conf()

    base_path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json')
    docs = expand_tree(base_path, '.json')

    if mask is not None:
        if mask.startswith('/'):
            mask = mask[1:]

        mask = os.path.join(base_path, mask)

    output = runner( jobs=report_jobs(docs, mask),
                     retval='results')

    if output_file is None:
        return output
    else:
        stats = [ _output_report_yaml(s) for s in output ]
        stats.append('...\n')
        if  output_file == 'print':
            for ln in stats:
                print(ln[:-1])
        else:
            with open(output_file, 'w') as f:
                for ln in stats:
                    f.write(ln)

## User facing fabric tasks

@task
def wc(mask=None):
    report = _generate_report(mask)

    count = 0
    for doc in report:
        count += doc['stats']['word-count']

    msg = "[stats]: there are {0} words".format(count)
    if mask is None:
        msg += ' total'
    else:
        msg += ' in ' + mask

    puts(msg)

    return count

@task
def report(fn=None):
    _generate_report(fn, output_file='print')

@task
def sweep(mask=None):
    puts('[stats]: starting full sweep of docs content.')
    conf = get_conf()

    out_file = _fn_output(mask, conf)

    _generate_report(mask, output_file=out_file, conf=conf)

    puts('[stats]: wrote full manual sweep to {0}'.format(out_file))

@task
def includes(mask=None):
    if mask == 'list':
        pprint(include().keys())
    elif mask is not None:
        if not mask.endswith('.rst'):
            mask += '.rst'

        if mask.startswith('source'):
            mask = mask[6:]

        if mask.startswith('/source'):
            mask = mask[7:]

        files = include()

        try:
           return pprint(files[mask])
        except ValueError:
            for pair in files.items():
                if pair[0].startswith(mask):
                    return pprint(files[pair[0]])

def include():
    conf = get_conf()
    source_dir = os.path.join(conf.build.paths.projectroot, conf.build.paths.source)
    grep = local('grep ".. include:: /" {0} -R'.format(source_dir), capture = True)

    rx = re.compile(source_dir + r'(.*):.*\.\. include:: (.*)')

    s = [rx.match(d).groups() for d in grep.split('\n')]
    def tuple_sort(k): return k[1]
    s.sort(key=tuple_sort)

    files = dict()

    for i in groupby(s, operator.itemgetter(1) ):
        files[i[0]] = list()
        for src in i[1]:
            files[i[0]].append(src[0])

    return files
