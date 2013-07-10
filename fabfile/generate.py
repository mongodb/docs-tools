import os.path
import sys

from multiprocessing import Pool
from utils import ingest_yaml_list, expand_tree, dot_concat
from fabric.api import task, puts, local
from make import check_dependency
from docs_meta import render_paths


def _generate_api_param(source, target):
    paths = render_paths('dict')
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'])))
    from rstcloth.param import generate_params

    r = generate_params(ingest_yaml_list(source))
    r.write(target)
    puts('[api]: rebuilt {0}'.format(target))

@task
def api():
    p = Pool()
    
    count = 0
    for source in expand_tree('source/reference', 'yaml'):
        target = dot_concat(os.path.splitext(source)[0], 'rst')
        if check_dependency(target, source):
            p.apply_async(_generate_api_param, args=(source, target))
            count += 1

    p.close()
    p.join()
    puts('[api]: generated {0} tables for api items'.format(str(count)))
