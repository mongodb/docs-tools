from fabric.api import task, local, env, puts
from droopy.factory import DroopyFactory
from droopy.lang.english import English
import json
import yaml

@task
def file(fn):
    env.input_file = fn

def report_statement(fn, test, number):
    puts("[stats]: '{0}' has a {1} of {2}".format(fn, test, number))

def _report(droopy):
    droopy.foggy_word_syllables = 3
    
    o = {
        'file': env.input_file,
        'stats': {
            'smog-index': droopy.smog,
            'flesch-level': droopy.flesch_grade_level,
            'flesch-ease': droopy.flesch_reading_ease,
            'coleman-liau': droopy.coleman_liau,
            'word-count': droopy.nof_words,
            'sentence-count': droopy.nof_sentences,
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

