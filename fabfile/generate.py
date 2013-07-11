import os.path
import sys

from multiprocessing import Pool
from utils import ingest_yaml_list, expand_tree, dot_concat, hyph_concat
from fabric.api import task, puts, local, env
from make import check_dependency
from docs_meta import render_paths

paths = render_paths('dict')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'])))
from rstcloth.param import generate_params
from rstcloth.toc import CustomTocTree
from rstcloth.table import TableBuilder, YamlTable, ListTable, RstTable

env.FORCE = False
@task
def force():
    env.FORCE = True

#################### API Param Table Generator ####################

### Internal Method

def _generate_api_param(source, target):
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
            # _generate_api_param(source, target)
            p.apply_async(_generate_api_param, args=(source, target))

            count +=1

    p.close()
    p.join()
    print('[api]: generated {0} tables for api items'.format(count))


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
    toc = CustomTocTree(fn)

    toc.build_contents()

    fmt = fn[16:19]

    if fmt.startswith('toc'):
        toc.build_dfn()
        toc.finalize()
        toc.dfn.write(_get_toc_output_name(base_name, 'dfn-list'))

    elif fmt.startswith('ref'):
        toc.build_table()
        toc.finalize()

        t = TableBuilder(RstTable(toc.table))
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

        if not fn.startswith('source/includes/table'):
            output_fn = _get_toc_output_name(base_name, 'toc')

            if env.FORCE or check_dependency(output_fn, fn):
                # _generate_toc_tree(fn, base_name, output_fn)
                p.apply_async(_generate_toc_tree, args=(fn, base_name, output_fn))
                count += 1

    p.close()
    p.join()

    print('[toc]: built {0} tables of contents'.format(count))

#################### Table Builder ####################

## Internal Supporting Methods

def _get_table_output_name(fn):
    return dot_concat(os.path.splitext(fn)[0], 'rst')
def _get_list_table_output_name(fn):
    return dot_concat(hyph_concat(os.path.splitext(fn)[0], 'list'), 'rst')

def _generate_tables(source, target, list_target):
    table_data = YamlTable(source)

    build_all = False
    if not table_data.format or table_data.format is None:
        build_all = True

    if build_all or table_data.format == 'list':
        list_table = TableBuilder(ListTable(table_data))
        list_table.write(list_target)
        puts('[table]: rebuilt {0}'.format(list_target))

        list_table.write(target)
        puts('[table]: rebuilt {0} as (a list table)'.format(target))

    # if build_all or table_data.format == 'rst':
    #     # this really ought to be RstTable, but there's a bug there.
    #     rst_table = TableBuilder(ListTable(table_data))
    #     rst_table.write(target)

    #     puts('[table]: rebuilt {0} as (a list table)'.format(target))

    print('[table]: rebuilt table output for {0}'.format(source))

## User facing fabric task

@task
def tables():
    p = Pool()

    count = 0
    for source in expand_tree(paths['includes'], 'yaml'):
        if os.path.basename(source).startswith('table'):

            target = _get_table_output_name(source)
            list_target = _get_list_table_output_name(source)

            if env.FORCE or check_dependency(target, source) or check_dependency(list_target, source):
                # _generate_tables(source, target, list_target)
                p.apply_async(_generate_tables, args=(source, target, list_target))
                count += 1

    p.close()
    p.join()

    print('[table]: built {0} tables'.format(count))
