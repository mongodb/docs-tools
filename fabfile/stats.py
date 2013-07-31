from fabric.api import task, local, env
from fabric.utils import puts, abort
from droopy.factory import DroopyFactory
from droopy.lang.english import English
from multiprocessing import Pool
from docs_meta import get_conf
from utils import expand_tree

import yaml
import json
import os.path

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
def _generate_report(mask, output_file, conf=None):
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

    output = [ _output_report_yaml(o.get()) for o in output ]

    if len(output) == 0:
        output[0] = output[0][4:]

    output.append('...\n')

    if output_file is None:
        for ln in output:
            print(ln[:-1])
    else:
        with open(output_file, 'w') as f:
            for ln in output:
                f.write(ln)

## User facing fabric tasks

@task
def report(fn=None):
    _generate_report(fn, None)

@task
def sweep(mask=None):
    puts('[stats]: starting full sweep of docs content.')
    conf = get_conf()

    out_file = _fn_output(mask, conf)

    _generate_report(mask, output_file=out_file, conf=conf)

    puts('[stats]: wrote full manual sweep to {0}'.format(out_file))
