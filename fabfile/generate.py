import os.path
import sys

from multiprocessing import Pool
from utils import ingest_yaml_list, expand_tree, dot_concat
from fabric.api import task, puts, local, env
from make import check_dependency
from docs_meta import render_paths

env.FORCE = False
@task
def force():
    env.FORCE = True

#################### API Param Table Generator #################### 

### Internal Method

def _generate_api_param(source, target):
    paths = render_paths('dict')
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'])))
    from rstcloth.param import generate_params

    r = generate_params(ingest_yaml_list(source))
    r.write(target)

    puts('[api]: rebuilt {0}'.format(target))

### User facing fabric task

@task
def api():
    p = Pool()
    
    count = 0
    for source in expand_tree('source/reference', 'yaml'):
        target = dot_concat(os.path.splitext(source)[0], 'rst')
        if env.FORCE or check_dependency(target, source):
            p.apply(_generate_api_param, args=(source, target))
            count +=1 

    p.close()
    p.join()
    puts('[api]: generated {0} tables for api items'.format(count))


#################### Table of Contents Generator #################### 

### Internal Methods

def _get_toc_base_name(fn):
    bn = os.path.basename(fn)

    if bn.startswith('ref-toc-'):
        return os.path.splitext(bn)[0][8:]
    if bn.startswith('toc-'):
        return os.path.splitext(bn)[0][4:]

def _get_toc_output_name(name, type):
    return 'source/includes/{0}-{1}.rst'.format(type, name)

def _generate_toc_tree(fn, base_name, toc_output):
    paths = render_paths('dict')
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'])))
    from rstcloth.toc import CustomTocTree

    toc = CustomTocTree(fn)

    toc.build_contents()

    fmt = fn[16:19]

    if fmt.startswith('toc'):
        toc.build_dfn()        
        toc.finalize()
        toc.dfn.write(_get_toc_output_name(base_name, 'dfn-list'))

    elif fmt.startswith('ref'):
        import rstcloth.table as tb
        toc.build_table()
        toc.finalize()

        t = tb.TableBuilder(tb.RstTable(toc.table))
        t.write(_get_toc_output_name(base_name, 'table'))
        
    toc.contents.write(toc_output)

    puts('[toc]: complied toc output for {0}'.format(fn))

### User facing fabric task

@task
def toc():
    p = Pool()

    count = 0
    for fn in expand_tree('source/includes', 'yaml'):
        base_name = _get_toc_base_name(fn)
        output_fn = _get_toc_output_name(base_name, 'toc')

        if env.FORCE or check_dependency(output_fn, fn):
            p.apply_async(_generate_toc_tree, args=(fn, base_name, output_fn))
            count += 1

    p.close()
    p.join()

    puts('[toc]: built {0} tables of contents'.format(count))
