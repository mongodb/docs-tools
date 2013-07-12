from fabric.api import task, local, env
from fabric.utils import puts, abort
from droopy.factory import DroopyFactory
from droopy.lang.english import English
from multiprocessing import Pool, Manager
from docs_meta import conf
from utils import expand_tree

import yaml
import json
import os.path

####### internal functions for rendering reports #######

def _render_report(fn=None):
    if fn is None:
        fn = env.input_file

    with open(os.path.abspath(fn), 'r') as f:
        text = json.load(f)['text']

    if 'source_file' not in env:
        base_fn, path, source = _fn_process(fn)
    else:
        source = env.source_file

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

def _fn_output(tag):
    fn = ['stats', 'sweep' ]
    if tag is not None:
        fn.append(tag.replace('/', '-'))
    fn.extend([conf.git.branches.current, conf.git.commit[:6]])

    out_fn = '.'.join(['-'.join(fn), 'yaml'])
    return os.path.join(conf.build.paths.output, out_fn)

env.input_file = None
def _resolve_input_file(fn):
    if fn.startswith('/'):
        fn = fn[1:]
    if fn.startswith('source'):
        fn = fn[7:]

    base_fn = os.path.splitext(fn)[0]
    path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json',
                        base_fn)
    source = '.'.join([os.path.join('source', base_fn), 'txt'])

    env.input_file = '.'.join([path, 'json'])
    env.source_file = source

    if not os.path.exists(env.input_file):
        abort("[stats]: processed json file does not exist for: {0}, build 'json-output' and try again.".format(source))

## YAML output wrapper

def _output_report_yaml(data):
   return yaml.safe_dump(data, default_flow_style=False, explicit_start=True)


########## user facing operations ##########

## Report Generator
def _generate_report(mask, output_file):
    base_path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json')
    docs = expand_tree(base_path, '.json')

    output = []

    p = Pool()

    for doc in docs:
        if doc.endswith('searchindex.json') or doc.endswith('globalcontext.json'):
            continue
        elif mask is None:
            output.append(p.apply_async( _render_report, kwds=dict(fn=doc)))
        else:
            if doc.startswith(os.path.join(base_path, mask)):
                output.append(p.apply_async( _render_report, kwds=dict(fn=doc)))

    p.close()
    p.join()

    output = [ _output_report_yaml(o.get()) for o in output ]
    output[0] = output[0][4:]
    output.append('...\n')

    if output_file is None:
        for ln in output:
            print ln[:-1]
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
    out_file = _fn_output(mask)

    _generate_report(mask, output_file=out_file)

    puts('[stats]: wrote full manual sweep to {0}'.format(out_file))
