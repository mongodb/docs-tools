from fabric.api import task, local, env
from fabric.utils import puts, abort
from droopy.factory import DroopyFactory
from droopy.lang.english import English

from docs_meta import conf

import yaml
import json
import os.path

@task
def file(fn):
    if fn.startswith('/'):
        fn = fn[1:]

    base_fn = os.path.splitext(fn)[0]
    path = os.path.join(conf.build.paths.output, conf.git.branches.current, 'json',
                        base_fn)

    env.input_file = '.'.join([path, 'json'])
    env.source_file = '.'.join([os.path.join('source', base_fn), '.txt'])

    if not os.path.exists(env.input_file):
        abort("[stats]: processed json file does not exist for: {0}, build 'json-output' and try again.".format(fn))


def _report(droopy):
    droopy.foggy_word_syllables = 3

    o = {
        'file': env.input_file,
        'source': env.source_file,
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
    puts(yaml.safe_dump(o,  default_flow_style=False, indent=3, explicit_start=True)[:-1])

@task
def report():
    with open(env.input_file, 'r') as f:
        document = f.read()

    droopy = DroopyFactory.create_full_droopy(document, English())

    _report(droopy)

@task
def jreport():
    with open(env.input_file, 'r') as f:
        text = json.loads(f.read())['text']

    droopy = DroopyFactory.create_full_droopy(text, English())

    _report(droopy)
