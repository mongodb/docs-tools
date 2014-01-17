import re
import collections

try:
    from utils.jobs.runners import runner
    from utils.files import copy_always
    from utils.errors import ProcessingError
    from utils.config import lazy_conf
    from utils.serialization import ingest_yaml
except ImportError:
    from jobs.runners import runner
    from files import copy_always
    from errors import ProcessingError
    from serialization import ingest_yaml
    from config import lazy_conf

def munge_page(fn, regex, out_fn=None,  tag='build'):
    with open(fn, 'r') as f:
        page = f.read()

    page = munge_content(page, regex)

    if out_fn is None:
        out_fn = fn

    with open(out_fn, 'w') as f:
        f.write(page)

    print('[{0}]: processed {1}'.format(tag, fn))

def munge_content(content, regex):
    if isinstance(regex, list):
        for cregex, subst in regex:
            content = cregex.sub(subst, content)
        return content
    else:
        return regex[0].sub(regex[1], content)


def process_page(fn, output_fn, regex, builder='processor'):
    tmp_fn = fn + '~'

    jobs = [
             {
               'target': tmp_fn,
               'dependency': fn,
               'job': munge_page,
               'args': dict(fn=fn, out_fn=tmp_fn, regex=regex),
             },
             {
               'target': output_fn,
               'dependency': tmp_fn,
               'job': copy_always,
               'args': dict(source_file=tmp_fn,
                            target_file=output_fn,
                            name=builder),
             }
           ]

    runner(jobs, pool=1, parallel=False, force=False)

def post_process_jobs(source_fn=None, tasks=None, conf=None):
    """
    input documents should be:

    {
      'transform': {
                     'regex': str,
                     'replace': str
                   }
      'type': <str>
      'file': <str|list>
    }

    ``transform`` can be either a document or a list of documents.
    """

    if tasks is None:
        conf = lazy_conf(conf)

        if source_fn is None:
            source_fn = os.path.join(conf.paths.project.root,
                                     conf.paths.builddata,
                                     'processing.yaml')
        tasks = ingest_yaml(source_fn)
    elif not isinstance(tasks, collections.Iterable):
        raise ProcessingError('[ERROR]: cannot parse post processing specification.')

    def rjob(fn, regex, type):
        return {
                 'target': fn,
                 'dependency': None,
                 'job': process_page,
                 'args': dict(fn=fn, output_fn=fn, regex=regex, builder=type)
               }

    for job in tasks:
        if not isinstance(job, dict):
            raise ProcessingError('[ERROR]: invalid replacement specification.')
        elif not 'file' in job and not 'transform' in job:
            raise ProcessingError('[ERROR]: replacement specification incomplete.')

        if 'type' not in job:
            job['type'] = 'processor'

        if isinstance(job['transform'], list):
            regex = [ (re.compile(rs['regex']), rs['replace'])
                      for rs in job['transform'] ]
        else:
            regex = (re.compile(job['transform']['regex']), job['transform']['replace'])

        if isinstance(job['file'], list):
            for fn in job['file']:
                yield rjob(fn, regex, job['type'])
        else:
            yield rjob(job['file'], regex, job['type'])

def truncate_file(fn, start_after=None, end_before=None):
    with open(fn, 'r') as f:
        source_lines = f.readlines()

    start_idx = 0
    end_idx = len(source_lines) - 1

    for idx, ln in enumerate(source_lines):
        if start_after is not None:
            if start_idx != 0 and ln.startswith(start_after):
                start_idx = idx - 1
                start_after = None

        if end_before is not None:
            if ln.startswith(end_before):
                end_idx = idx
                break

    with open(fn, 'w') as f:
        f.writelines(source_lines[start_idx:end_idx])
