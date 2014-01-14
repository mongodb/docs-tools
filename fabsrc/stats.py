import json
import operator
import os.path
import re
import json

from itertools import groupby
from multiprocessing import Pool

from fabric.api import task, local, env
from fabric.utils import puts, abort

from droopy.factory import DroopyFactory
from droopy.lang.english import English
from droopy import Droopy, attr, op

from docs_meta import get_conf
from utils import expand_tree, AttributeDict, ingest_yaml_doc, ingest_yaml_list
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
        'report': 'file',
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

    return r

## Path and filneame processing

def _fn_output(tag, conf=None):
    if conf is None:
        conf = get_conf()

    fn = ['stats', 'sweep' ]
    if tag is not None:
        fn.append(tag.replace('/', '-'))
    fn.extend([conf.git.branches.current, conf.git.commit[:6]])

    out_fn = '.'.join(['-'.join(fn), 'json'])
    return os.path.join(conf.build.paths.output, out_fn)

def _resolve_input_file(fn):
    if fn.startswith('/'):
        fn = fn[1:]
    if fn.startswith('source'):
        fn = fn[7:]

    base_fn = os.path.splitext(fn)[0]
    source = '.'.join([os.path.join('source', base_fn), 'txt'])

    return base_fn, source

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
def _generate_report(mask, output_file=None, conf=None, data=None):
    if conf is None:
        conf = get_conf()

    base_path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json')
    docs = expand_tree(base_path, '.json')

    if mask is not None:
        if mask.startswith('/'):
            mask = mask[1:]

        mask = os.path.join(base_path, mask)

    if data is None:
        output = runner( jobs=report_jobs(docs, mask),
                         retval='results')
    else:
        output = data

    if output_file is None:
        return output
    else:
        if output_file == 'print':
            puts(json.dumps(output, indent=2))
        else:
            with open(output_file, 'w') as f:
                json.dump(output, f)

## User facing fabric tasks

@task
def wc(mask=None):
    "Returns a total word count for the entire resource as rendered."

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
    "Returns a statistics per file, for a specific file or group of files."

    data = _generate_report(fn)
    if len(data) > 1:
        data.append(multi(fn, data, None))

    puts(json.dumps(data, indent=3))

def sum_key(key, data, sub=None):
    r = 0
    for d in data:
        if sub is not None:
            d = d[sub]

        try:
            r += d[key]
        except TypeError:
            r += d[key]['count']
    return r

@task
def multi(mask=None, data=None, output_file='print'):
    "Takes a 'mask' and returns aggregated statistics for a group of documents."

    if data is None:
        data = _generate_report(mask)

    n = len(data)

    o = dict()

    keys = [ "flesch-ease", "sentence-count", "word-count",
             "smog-index", "sentence-len-avg", "flesch-level",
             "coleman-liau", "passives", "foggy", "weasels" ]

    for key in keys:
        o[key] = sum_key(key, data, 'stats')

    r = dict()
    for k,v in o.iteritems():
        r[k] = float(v)/n if n > 0 else float('nan')

    r['word-count'] = int(r['word-count'])
    r['sentence-len-avg'] = int(r['sentence-len-avg'])

    o = { 'report': 'multi',
          'mask': mask if mask is not None else "all",
          'averages': r,
          'totals': {
              'passive': o['passives'],
              'foggy': o['foggy'],
              'weasel': o['weasels'],
              'word-count': o['word-count']
              }
          }

    if output_file is None:
        return o
    elif output_file == 'print':
        puts(json.dumps(o, indent=3, sort_keys=True))
    else:
        json.dump(o, output_file, indent=3)
