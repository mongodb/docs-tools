from fabric.api import task, local, env
from fabric.utils import puts, abort
from droopy.factory import DroopyFactory
from droopy.lang.english import English

from docs_meta import conf
from utils import expand_tree

import yaml
import json
import os.path

####### internal functions for rendering reports #######

def render_report(fn=None):
    if fn is None:
        fn = env.input_file

    with open(fn, 'r') as f:
        text = json.loads(f.read())['text']
        
    base_fn, path, source = _fn_process(fn)
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

def output_report(data, fmt='yaml'):
    if fmt == 'yaml':
        puts(yaml.safe_dump(data,  default_flow_style=False, indent=3, explicit_start=True)[:-1])
    elif fmt == 'json':
        puts(json.dumps(data, indent=2))
        
def _fn_process(fn):
    base_fn = os.path.splitext(fn)[0]
    path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json',
                        base_fn)
    source = '.'.join([os.path.join('source', base_fn), 'txt'])

    return path, base_fn, source

def _fn_output():
    out_fn = '.'.join(['-'.join(['stats', 'sweep', conf.git.branches.current, conf.git.commit[:6]]), 'yaml'])
    return os.path.join(conf.build.paths.output, out_fn)

########## user facing operations ##########

env.input_file = None

@task(aliases=['file', 'input'])
def input_file(fn):
    if fn.startswith('/'):
        fn = fn[1:]
    if fn.startswith('source'):
        fn = fn[7:]

    base_fn, path, source = _fn_process(fn)

    env.input_file = '.'.join([path, 'json'])
    env.source_file = source

    if not os.path.exists(env.input_file):
        abort("[stats]: processed json file does not exist for: {0}, build 'json-output' and try again.".format(fn))

@task
def report(fn=None, fmt='yaml'):
    if fn is None and env.input_file is None:
        abort('[stats]: must specify a file to report stats.')
    else:
        input_file(fn)
        
    output_report(render_report())

@task
def sweep():
    docs = expand_tree(os.path.join(conf.build.paths.output, conf.git.branches.current, 'json'), 'json')

    output = []

    puts('[stats]: starting full sweep of docs content.')
    for doc in docs: 
        if doc.endswith('searchindex.json') or doc.endswith('globalcontext.json'):
            pass
        else:
            output.append(yaml.safe_dump(render_report(doc), default_flow_style=False, explicit_start=True))

    output[0] = output[0][4:]
    output.append('...\n')

    out_file = _fn_output()
    
    with open(out_file, 'w') as f:
        for ln in output:
            f.write(ln)
    puts('[stats]: wrote full manual sweep to {0}'.format(out_file))

@task    
def sweep_report():
    local(' '.join(['cat', _fn_output()]))
