import os.path
from copy import copy

from utils.files import expand_tree
from utils.rstcloth.toc import CustomTocTree, AggregatedTocTree
from utils.rstcloth.table import TableBuilder, RstTable

#################### Table of Contents Generator ####################

### Internal Methods

def _get_toc_base_name(fn):
    bn = os.path.basename(fn)

    if bn.startswith('ref-toc-'):
        return os.path.splitext(bn)[0][8:]
    elif bn.startswith('toc-') or bn.startswith('ref-spec-'):
        return os.path.splitext(bn)[0][4:]

def _get_toc_output_name(name, type, paths):
    if type == 'toc':
        return os.path.join(paths.branch_source, 'includes', 'toc', '{0}.rst'.format(name))
    else:
        return os.path.join(paths.branch_source, 'includes', 'toc', '{0}-{1}.rst'.format(type, name))

def _generate_toc_tree(fn, fmt, base_name, paths, conf):
    print('[toc]: generating {0} toc'.format(fn))

    if fmt == 'spec':
        toc = AggregatedTocTree(fn, conf)
        fmt = toc._first_source[0:3]
        toc.build_dfn()
        toc.build_table()
        toc.finalize()

        if fmt == 'ref':
            if toc.table is not None:
                outfn = _get_toc_output_name(base_name, 'table', paths)
                t = TableBuilder(RstTable(toc.table))
                t.write(outfn)
                print('[toc-spec]: wrote: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            print('[toc-spec]: wrote: '  + outfn)

    else:
        toc = CustomTocTree(fn, conf)
        toc.build_contents()

        if fmt == 'toc':
            toc.build_dfn()
        elif fmt == 'ref':
            toc.build_table()

        toc.finalize()

        outfn = _get_toc_output_name(base_name, 'toc', paths)
        toc.contents.write(outfn)
        print('[toc]: wrote: '  + outfn)

        if fmt == 'ref':
            outfn = _get_toc_output_name(base_name, 'table', paths)
            t = TableBuilder(RstTable(toc.table))
            t.write(outfn)
            print('[ref-toc]: wrote: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            print('[toc]: wrote: '  + outfn)

    print('[toc]: compiled toc output for {0}'.format(fn))

def toc_jobs(conf):
    paths = copy(conf.paths)

    for fn in expand_tree(paths.includes, 'yaml'):
        if fn.startswith(os.path.join(paths.includes, 'table')):
            continue
        elif fn.startswith(os.path.join(paths.includes, 'step')):
            continue
        elif len(fn) >= 24:
            base_name = _get_toc_base_name(fn)

            fmt = fn[20:24]
            if fmt != 'spec':
                fmt = fn[16:19]

            o = {
                  'dependency': os.path.join(paths.projectroot, fn),
                  'job': _generate_toc_tree,
                  'target': [],
                  'args': [fn, fmt, base_name, paths, conf]
                }

            if fmt != 'spec':
                o['target'].append(_get_toc_output_name(base_name, 'toc', paths))

            is_ref_spec = fn.startswith(os.path.join(os.path.dirname(fn), 'ref-spec'))

            if not is_ref_spec and (fmt == 'toc' or fmt == 'spec'):
                o['target'].append(_get_toc_output_name(base_name, 'dfn-list', paths))
            elif fmt == 'ref' or is_ref_spec:
                o['target'].append(_get_toc_output_name(base_name, 'table', paths))
           
            yield o
