import os.path
import re

from itertools import groupby
from operator import itemgetter

try:
    from utils.serialization import ingest_yaml_doc, ingest_yaml_list
    from utils.files import expand_tree
    from utils.shell import command
except ImportError:
    from serialization import ingest_yaml_doc, ingest_yaml_list
    from files import expand_tree
    from shell import command

def include_files(conf, files=None):
    if files is not None:
        return files
    else:
        source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)
        grep = command('grep -R ".. include:: /" {0} || exit 0'.format(source_dir), capture=True).out

        rx = re.compile(source_dir + r'(.*):.*\.\. include:: (.*)')

        s = [ m.groups()
              for m in [ rx.match(d)
                         for d in grep.split('\n') ]
              if m is not None
            ]

        def tuple_sort(k):
            return k[1]
        s.sort(key=tuple_sort)

        files = dict()

        for i in groupby(s, itemgetter(1)):
            files[i[0]] = set()
            for src in i[1]:
                if not src[0].endswith('~') and not src[0].endswith('overview.rst'):
                    files[i[0]].add(src[0])
            files[i[0]] = list(files[i[0]])
            files[i[0]].sort()

        files.update(generated_includes(conf))

        return files

def included_once(conf, inc_files=None):
    results = []
    for file, includes in include_files(conf=conf, files=inc_files).items():
        if len(includes) == 1:
            results.append(file)
    return results

def included_recusively(conf, inc_files=None):
    files = include_files(conf=conf, files=inc_files)
    # included_files is a py2ism, depends on it being an actual list
    included_files = files.keys()

    results = {}
    for inc, srcs in files.items():
        for src in srcs:
            if src in included_files:
                results[inc] = srcs
                break

    return results

def includes_masked(mask, conf, inc_files=None):
    files = include_files(conf=conf, files=inc_files)

    results = {}
    try:
        m = mask + '.rst'
        results[m] = files[m]
    except (ValueError, KeyError):
        for pair in files.items():
            if pair[0].startswith(mask):
                results[pair[0]] = pair[1]

    return results


def generated_includes(conf):
    toc_spec_files = []
    step_files = []
    for fn in expand_tree(os.path.join(conf.paths.includes), input_extension='yaml'):
        base = os.path.basename(fn)

        if base.startswith('toc-spec'):
            toc_spec_files.append(fn)
        elif base.startswith('ref-spec'):
            toc_spec_files.append(fn)
        elif base.startswith('steps'):
            step_files.append(fn)

    maskl = len(conf.paths.source)
    path_prefix = conf.paths.includes[len(conf.paths.source):]
    mapping = {}
    for spec_file in toc_spec_files:
        if os.path.exists(spec_file):
            data = ingest_yaml_doc(spec_file)
        else:
            continue

        deps = [ os.path.join(path_prefix, i ) for i in data['sources']]

        mapping[spec_file[maskl:]] = deps

    for step_def in step_files:
        data = ingest_yaml_list(step_def)

        deps = []
        for step in data:
            if 'source' in step:
                deps.append(step['source']['file'])

        if len(deps) != 0:
            deps = [ os.path.join(path_prefix, i ) for i in deps ]

            mapping[step_def[maskl:]] = deps

    return mapping

def include_files_unused(conf, inc_files=None):
    inc_files = [ fn[6:] for fn in expand_tree(os.path.join(conf.paths.includes), None) ]
    mapping = include_files(conf=conf)

    results = []
    for fn in inc_files:
        if fn.endswith('yaml') or fn.endswith('~'):
            continue
        if fn not in mapping.keys():
            results.append(fn)

    return results

def changed_includes(conf):
    from pygit2 import Repository, GIT_STATUS_CURRENT, GIT_STATUS_IGNORED

    repo_path = conf.paths.projectroot

    r = Repository(repo_path)

    changed = []
    for path, flag in r.status().items():
        if flag not in [ GIT_STATUS_CURRENT, GIT_STATUS_IGNORED ]:
            if path.startswith('source/'):
                if path.endswith('.txt') or path.endswith('.rst'):
                    changed.append(path[6:])

    source_path = os.path.join(conf.paths.source, conf.paths.output, conf.git.branches.current, 'json')
    changed_report = []

    for fn in include_files(conf):
        if fn in changed:
            changed_report.append(fn)

    return changed_report
