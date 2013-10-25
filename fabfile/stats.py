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

from docs_meta import get_conf
from utils import expand_tree

####### internal functions for rendering reports #######

def _render_report(fn):
    with open(os.path.abspath(fn), 'r') as f:
        text = json.load(f)['text']

    base_fn, source = _resolve_input_file(fn)

    droopy = DroopyFactory.create_full_droopy(text, English())
    droopy.foggy_word_syllables = 3

    return {
        'file': fn,
        'source': source,
        'stats': {
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

## Report Generator
def _generate_report(mask, output_file=None, conf=None):
    if conf is None:
        conf = get_conf()

    base_path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json')
    docs = expand_tree(base_path, '.json')

    if mask is not None and mask.startswith('/'):
        mask = mask[1:]

    output = []

    p = Pool()

    for doc in docs:
        if doc.endswith('searchindex.json') or doc.endswith('globalcontext.json'):
            continue
        elif mask is None:
            output.append(p.apply_async( _render_report, kwds=dict(fn=doc)))
        else:
            if doc.startswith(os.path.join(base_path, mask)):
                output.append(p.apply_async( _render_report, args=(doc,)))

    p.close()
    p.join()

    stats = [ _output_report_yaml(o.get()) for o in output ]

    if len(stats) == 0:
        stats[0] = stats[0][4:]

    stats.append('...\n')

    if output_file is None:
        return (o.get() for o in output )
    elif output_file == 'print':
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

        pprint(include(mask))

def include(mask=None):
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

    if mask is not None:
        try:
           return files[mask]
        except ValueError:
            for pair in files.items():
                if pair[0].startswith(mask):
                    return files[pair[0]]
    else:
        return files
