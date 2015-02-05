import sys
import logging
import os.path
import string
import random
import yaml

logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.INFO)

from giza.tools.files import expand_tree
from libgiza.app import BuildApp

if sys.version_info >= (3, 0):
    basestring = str

def get_enclosing_file(tocs, fn):
    for source_fn in tocs:
        for entry in tocs[source_fn]:
            if entry['file'] == fn:
                return os.path.basename(source_fn)

    raise TypeError

def main():
    files = expand_tree('source/includes/', 'yaml')

    spec_fns = []
    toc_fns = []

    for fn in files:
        if 'ref-spec' in fn:
            spec_fns.append(fn)
        elif 'toc' not in fn:
            continue
        elif 'spec-new' in fn:
            continue
        elif 'spec' in fn:
            spec_fns.append(fn)
        else:
            toc_fns.append(fn)

    logger.info('have {0} spec files'.format(len(spec_fns)))
    logger.info('have {0} toc files'.format(len(toc_fns)))

    specs = {}
    tocs = {}

    for fn in spec_fns:
        try:
            with open(fn, 'r') as f:
                specs[fn] = [ d for d in yaml.safe_load_all(f) if d is not None][0]
        except:
            continue

    for fn in toc_fns:
        with open(fn, 'r') as f:
            tocs[fn] = [ d for d in yaml.safe_load_all(f) if d is not None]

    logger.info('have {0} spec files'.format(len(specs)))
    logger.info('have {0} toc files'.format(len(tocs)))

    new_specs = {}
    for fn in specs:
        new_spec = []
        spec = specs[fn]
        new_specs[fn] = new_spec

        for entry in spec['files']:
            new_entry = {}
            new_spec.append(new_entry)

            if 'level' in entry:
                new_entry['level'] = entry['level']
            else:
                new_entry['level'] = 1


            if isinstance(entry, basestring):
                entry = { 'file': entry }

            if 'file' in entry:
                new_entry['source'] = {
                    'file': get_enclosing_file(tocs, entry['file']),
                    'ref': entry['file']
                }
            else:
                new_entry['text_only'] = True
                new_entry['description'] = entry['text']
                new_entry['ref'] = "".join( [random.choice(string.letters) for i in xrange(15)] )

        with open(fn, 'w') as f:
            yaml.safe_dump_all(new_spec, f, default_flow_style=False)
            logger.info('wrote: ' + fn)

if __name__ == '__main__':
    main()
