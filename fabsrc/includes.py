import re
import json
import os.path
import operator

from itertools import groupby

from fabric.api import local, task

from utils.config import lazy_conf
from utils.files import expand_tree
from utils.serialization import ingest_yaml_doc, ingest_yaml_list

@task
def names():
    "Returns the names of all included files as a list."

    render_for_console(include_files().keys())

@task
def graph():
    "Returns the full directed dependency graph for a all included files."

    render_for_console(include_files())

@task
def recursive():
    "Returns a list of included files that include other files."

    render_for_console(included_recusively())

@task
def single():
    "Returns a list of included files that are only used once."

    render_for_console(included_once())

@task
def unused():
    "Returns a list of included files that are never used."

    render_for_console(include_files_unused())

@task
def filter(mask):
    "Returns a subset of the dependency graph based on a required 'mask' argument."

    mask = resolve_mask(mask)

    render_for_console(includes_masked(mask))

@task
def changed():
    "Returns a list of all files that include a file that has changed since the last commit."
    render_for_console(changed_includes())

########## Helper Functions ##########

def resolve_mask(mask):
    if mask.startswith('source'):
        mask = mask[6:]
    if mask.startswith('/source'):
        mask = mask[7:]

    return mask

def render_for_console(data):
    if not isinstance(data, list):
        data = list(data)

    print(json.dumps(data, indent=3))

########## Worker Function ##########

def included_once(inc_files=None):
    results = []
    for file, includes in include_files(inc_files).items():
        if len(includes) == 1:
            results.append(file)
    return results

def included_recusively(inc_files=None):
    files = include_files(inc_files)
    # included_files is a py2ism, depends on it being an actual list
    included_files = files.keys()

    results = {}
    for inc, srcs in files.items():
        for src in srcs:
            if src in included_files:
                results[inc] = srcs
                break

    return results

def includes_masked(mask, inc_files=None):
    files = include_files(inc_files)

    results = {}
    try:
        m = mask + '.rst'
        results[m] = files[m]
    except (ValueError, KeyError):
        for pair in files.items():
            if pair[0].startswith(mask):
                results[pair[0]] = pair[1]

    return results

def include_files(files=None, conf=None):
    if files is not None:
        return files
    else:
        conf = lazy_conf(conf)

        source_dir = os.path.join(conf.paths.projectroot, conf.paths.source)
        grep = local('grep -R ".. include:: /" {0} || exit 0'.format(source_dir), capture=True)

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

        for i in groupby(s, operator.itemgetter(1) ):
            files[i[0]] = set()
            for src in i[1]:
                if not src[0].endswith('~'):
                    files[i[0]].add(src[0])
            files[i[0]] = list(files[i[0]])

        files.update(generated_includes(conf))

        return files

def generated_includes(conf=None):
    conf = lazy_conf(conf)

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
        data = ingest_yaml_doc(spec_file)
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

def include_files_unused(inc_files=None, conf=None):
    conf = lazy_conf(conf)

    inc_files = [ fn[6:] for fn in expand_tree(os.path.join(conf.paths.includes), None) ]
    mapping = include_files(conf)

    results = []
    for fn in inc_files:
        if fn.endswith('yaml') or fn.endswith('~'):
            continue
        if fn not in mapping.keys():
            results.append(fn)

    return results

def changed_includes(conf=None):
    from pygit2 import Repository, GIT_STATUS_CURRENT, GIT_STATUS_IGNORED
    conf = lazy_conf(conf)

    repo_path = conf.paths.projectroot

    r = Repository(repo_path)

    changed = []
    for path, flag in r.status().items():
        if flag not in [ GIT_STATUS_CURRENT, GIT_STATUS_IGNORED ]:
            if path.startswith('source/'):
                if path.endswith('.txt'):
                    changed.append(path[6:])

    source_path = os.path.join(conf.paths.source, conf.paths.output, conf.git.branches.current, 'json')
    changed_report = []

    for report in _generate_report(None):
        if report['source'][len(source_path):] in changed:
            changed_report.append(report)

    if not len(changed_report) == 0:
        changed_report.append(multi(data=changed_report, output_file=None))

    return changed_report
