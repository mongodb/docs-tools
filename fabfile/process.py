import collections
import json
import os
import re
import shutil
import subprocess

from multiprocessing import cpu_count

from fabric.api import task, env, abort, puts, local

from docs_meta import output_yaml, get_manual_path, get_conf
from utils import md5_file, symlink, expand_tree, dot_concat, ingest_yaml_list, munge_content, munge_page

from make import check_hashed_dependency, check_dependency, runner
from includes import include_files

env.input_file = None
env.output_file = None

@task
def input(fn):
    env.input_file = fn

@task
def output(fn):
    env.output_file = fn

########## Process Sphinx Json Output ##########

def json_output(conf=None):
    if conf is None:
        conf = get_conf()

    list_file = os.path.join(conf.build.paths.branch_staging, 'json-file-list')
    public_list_file = os.path.join(conf.build.paths.public_site_output,
                                    'json', '.file_list')

    cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {src} {dst}'
    json_dst = os.path.join(conf.build.paths.public_site_output, 'json')

    if not os.path.exists(json_dst):
        os.makedirs(json_dst)

    local(cmd.format(src=os.path.join(conf.build.paths.branch_output, 'json') + '/',
                     dst=json_dst))

    copy_if_needed(list_file, public_list_file)
    puts('[json]: deployed json files to local staging.')

def json_output_jobs(conf=None):
    if conf is None:
        conf = get_conf()

    regexes = [
        (re.compile(r'<a class=\"headerlink\"'), '<a'),
        (re.compile(r'<[^>]*>'), ''),
        (re.compile(r'&#8220;'), '"'),
        (re.compile(r'&#8221;'), '"'),
        (re.compile(r'&#8216;'), "'"),
        (re.compile(r'&#8217;'), "'"),
        (re.compile(r'&#\d{4};'), ''),
        (re.compile(r'&nbsp;'), ''),
        (re.compile(r'&gt;'), '>'),
        (re.compile(r'&lt;'), '<')
    ]

    outputs = []
    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>

        path = os.path.join(conf.build.paths.branch_output,
                            'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])
        fjson = dot_concat(path, 'fjson')
        json = dot_concat(path, 'json')

        if conf.project.name == 'mms':
            if not os.path.exists(fjson):
                continue

        yield dict(target=json,
                   dependency=fjson,
                   job=process_json_file,
                   args=(fjson, json, regexes, conf))

        outputs.append(json)

    list_file = os.path.join(conf.build.paths.branch_staging, 'json-file-list')

    yield dict(target=list_file,
               dependency=None,
               job=generate_list_file,
               args=(outputs, list_file, conf))

def process_json_file(input_fn, output_fn, regexes, conf=None):
    with open(input_fn, 'r') as f:
        document = f.read()

    doc = json.loads(document)

    if 'body' in doc:
        text = doc['body'].encode('ascii', 'ignore')
        text = munge_content(text, regexes)

        doc['text'] = ' '.join(text.split('\n')).strip()

    if 'title' in doc:
        title = doc['title'].encode('ascii', 'ignore')
        title = munge_content(title, regexes)

        doc['title'] = title

    url = [ conf.project.url, conf.project.basepath ]
    url.extend(input_fn.rsplit('.', 1)[0].split(os.path.sep)[3:])

    doc['url'] = '/'.join(url) + '/'

    with open(output_fn, 'w') as f:
        f.write(json.dumps(doc))

def generate_list_file(outputs, path, conf=None):
    dirname = os.path.dirname(path)

    if conf is None:
        conf = get_conf()

    url = '/'.join([ conf.project.url, conf.project.basepath, 'json' ])

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(path, 'w') as f:
        for fn in outputs:
            f.write( '/'.join([ url, fn.split('/', 3)[3:][0]]) )
            f.write('\n')

    puts('[json]: rebuilt inventory of json output.')

########## Update Dependencies ##########

def update_dependency(fn):
    if os.path.exists(fn):
        os.utime(fn, None)

def refresh_dependency_jobs(conf):
    graph = include_files()

    if not os.path.exists(conf.build.system.dependency_cache):
        dep_map = None
    else:
        with open(conf.build.system.dependency_cache, 'r') as f:
            dep_cache = json.load(f)
            dep_map = dep_cache['files']

    for target, deps in graph.items():
        yield {
            'job': dep_refresh_worker,
            'args': [target, deps, dep_map, conf],
            'target': None,
            'dependency': None
        }

def dep_refresh_worker(target, deps, dep_map, conf):
    if check_hashed_dependency(target, deps, dep_map) is True:
        target = os.path.join(conf.build.paths.projectroot,
                              conf.build.paths.branch_source,
                              target[1:])

        update_dependency(target)
        return 1
    else:
        return 0

def refresh_dependencies(conf=None):
    if conf is None:
        conf = get_conf()

    return sum(runner(refresh_dependency_jobs(conf), retval='results', parallel='process'))

########## Main Output Processing Targets ##########

class InvalidPath(Exception): pass

def copy_always(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False:
        puts("[{0}]: Input file '{1}' does not exist.".format(name, source_file))
        raise InvalidPath
    else:
        if not os.path.exists(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

    puts('[{0}]: copied {1} to {2}'.format(name, source_file, target_file))

def copy_if_needed(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False or os.path.isdir(source_file):
        puts("[{0}]: Input file '{1}' does not exist.".format(name, source_file))
        raise InvalidPath
    elif os.path.isfile(target_file) is False:
        if not os.path.exists(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

        if name is not None:
            puts('[{0}]: created "{1}" which did not exist.'.format(name, target_file))
    else:
        if md5_file(source_file) == md5_file(target_file):
            if name is not None:
                puts('[{0}]: "{1}" not changed.'.format(name, source_file))
        else:
            shutil.copyfile(source_file, target_file)

            if name is not None:
                puts('[{0}]: "{1}" changed. Updated: {2}'.format(name, source_file, target_file))

@task
def create_link():
    _create_link(env.input_file, env.output_file)

def _create_link(input_fn, output_fn):
    out_dirname = os.path.dirname(output_fn)
    if out_dirname != '' and not os.path.exists(out_dirname):
        os.makedirs(out_dirname)

    if os.path.islink(output_fn):
        os.remove(output_fn)
    elif os.path.isdir(output_fn):
        abort('[{0}]: {1} exists and is a directory'.format('link', output_fn))
    elif os.path.exists(output_fn):
        abort('[{0}]: could not create a symlink at {1}.'.format('link', output_fn))

    out_base = os.path.basename(output_fn)
    if out_base == "":
       abort('[{0}]: could not create a symlink at {1}.'.format('link', output_fn))
    else:
        symlink(out_base, input_fn)
        os.rename(out_base, output_fn)
        puts('[{0}] created symbolic link pointing to "{1}" named "{2}"'.format('symlink', input_fn, out_base))

def manual_single_html(input_file, output_file):
    # don't rebuild this if its not needed.
    if check_dependency(output_file, input_file) is True:
        pass
    else:
        puts('[process] [single]: singlehtml not changed, not reprocessing.')
        return False

    with open(input_file, 'r') as f:
        text = f.read()

    text = re.sub('href="contents.html', 'href="index.html', text)
    text = re.sub('name="robots" content="index"', 'name="robots" content="noindex"', text)
    text = re.sub('(href=")genindex.html', '\1../genindex/', text)

    with open(output_file, 'w') as f:
        f.write(text)

    puts('[process] [single]: processed singlehtml file.')

#################### PDFs from Latex Produced by Sphinx  ####################

def _clean_sphinx_latex(fn, regexes):
    with open(fn, 'r') as f:
        tex = f.read()

    for regex, subst in regexes:
        tex = regex.sub(subst, tex)

    with open(fn, 'w') as f:
        f.write(tex)

    puts('[pdf]: processed Sphinx latex format for {0}'.format(fn))

def _render_tex_into_pdf(fn, path):
    pdflatex = 'TEXINPUTS=".:{0}:" pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False

    puts('[pdf]: completed pdf rendering stage 1 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call("makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, os.path.basename(fn)[:-4]), shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
    puts('[pdf]: completed pdf rendering stage 2 of 4 (indexing) for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    puts('[pdf]: completed pdf rendering stage 3 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessErro:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    puts('[pdf]: completed pdf rendering stage 4 of 4 for: {0}'.format(fn))

    puts('[pdf]: rendered {0}.{1}'.format(os.path.basename(fn), 'pdf'))

@task
def pdfs():
    "Processes '.tex' files and runs 'pdflatex' to generate all PDFs."
    pdf_worker()

def pdf_worker(conf=None):
    if conf is None:
        conf = get_conf()

    for it, queue in enumerate(pdf_jobs(conf)):
        count = runner(queue)
        puts("[pdf]: completed {0} pdf jobs, in stage {1}".format(count, it))

def pdf_jobs(conf):
    pdfs = ingest_yaml_list(os.path.join(conf.build.paths.builddata, 'pdfs.yaml'))
    tex_regexes = [ ( re.compile(r'(index|bfcode)\{(.*)--(.*)\}'),
                      r'\1\{\2-\{-\}\3\}'),
                    ( re.compile(r'\\PYGZsq{}'), "'"),
                    ( re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv)'),
                      r'\code{' + conf.project.url + r'/' + conf.project.tag) ]

    # this is temporary
    queue = ( [], [], [], [], [] )

    for i in pdfs:
        tagged_name = i['output'][:-4] + '-' + i['tag']
        deploy_fn = tagged_name + '-' + conf.git.branches.current + '.pdf'
        link_name = deploy_fn.replace('-' + conf.git.branches.current, '')

        if 'edition' in i:
            deploy_path = os.path.join(conf.build.paths.public, i['edition'])
            if i['edition'] == 'hosted':
                deploy_path = os.path.join(deploy_path,  conf.git.branches.current)
                latex_dir = os.path.join(conf.build.paths.output, i['edition'],
                                         conf.git.branches.current, 'latex')
            else:
                latex_dir = os.path.join(conf.build.paths.output, i['edition'], 'latex')
                deploy_fn = tagged_name + '.pdf'
                link_name = deploy_fn
        else:
            deploy_path = conf.build.paths['branch-staging']
            latex_dir = os.path.join(conf.build.paths['branch-output'], 'latex')

        i['source'] = os.path.join(latex_dir, i['output'])
        i['processed'] = os.path.join(latex_dir, tagged_name + '.tex')
        i['pdf'] = os.path.join(latex_dir, tagged_name + '.pdf')
        i['deployed'] = os.path.join(deploy_path, deploy_fn)
        i['link'] = os.path.join(deploy_path, link_name)
        i['path'] = latex_dir

        # these appends will become yields, once runner() can be dependency
        # aware.
        queue[0].append(dict(dependency=None,
                             target=i['source'],
                             job=_clean_sphinx_latex,
                             args=(i['source'], tex_regexes)))

        queue[1].append(dict(dependency=i['source'],
                             target=i['processed'],
                             job=copy_if_needed,
                             args=(i['source'], i['processed'], 'pdf')))

        queue[2].append(dict(dependency=i['processed'],
                             target=i['pdf'],
                             job=_render_tex_into_pdf,
                             args=(i['processed'], i['path'])))

        queue[3].append(dict(dependency=i['pdf'],
                             target=i['deployed'],
                             job=copy_if_needed,
                             args=(i['pdf'], i['deployed'], 'pdf')))

        if i['link'] != i['deployed']:
            queue[4].append(dict(dependency=i['deployed'],
                                 target=i['link'],
                                 job=_create_link,
                                 args=(deploy_fn, i['link'])))

    return queue

#################### Error Page Processing ####################

# this is called directly from the sphinx generation function in sphinx.py.

def error_pages():
    conf = get_conf()

    error_conf = os.path.join(conf.build.paths.builddata, 'errors.yaml')

    if not os.path.exists(error_conf):
        return None
    else:
        error_pages = ingest_yaml_list(error_conf)

        sub = (re.compile(r'\.\./\.\./'), conf.project.url + r'/' + conf.project.tag + r'/')

        for error in error_pages:
            page = os.path.join(conf.build.paths.projectroot,
                                conf.build.paths['branch-output'], 'dirhtml',
                                'meta', error, 'index.html')
            munge_page(fn=page, regex=sub, tag='error-pages')

        puts('[error-pages]: rendered {0} error pages'.format(len(error_pages)))

#################### Gettext Processing ####################

def gettext_jobs(conf=None):
    if conf is None:
        conf = get_conf()

    locale_dirs = os.path.join(conf.build.paths.projectroot,
                               conf.build.paths.locale, 'pot')

    branch_output = os.path.join(conf.build.paths.projectroot,
                                       conf.build.paths.branch_output,
                                       'gettext')

    path_offset = len(branch_output) + 1

    for fn in expand_tree(branch_output, None):
        yield {
            'job': copy_if_needed,
            'args': [ fn, os.path.join(locale_dirs, fn[path_offset:]), None]
        }

#################### Manpage Processing ####################

def manpage_url(regex_obj, input_file=None):
    if input_file is None:
        if env.input_file is None:
            abort('[man]: you must specify input and output files.')
        else:
            input_file = env.input_file

    with open(input_file, 'r') as f:
        manpage = f.read()

    if isinstance(regex_obj, list):
        for regex, subst in regex_obj:
            manpage = regex.sub(subst, manpage)
    else:
        manpage = regex_obj[0].sub(regex_obj[1], manpage)

    with open(input_file, 'w') as f:
        f.write(manpage)

    puts("[{0}]: fixed urls in {1}".format('man', input_file))

def manpage_url_jobs(conf):
    project_source = os.path.join(conf.build.paths.projectroot,
                                  conf.build.paths.source)

    top_level_items = set()
    for fs_obj in os.listdir(project_source):
        if fs_obj.startswith('.static') or fs_obj == 'index.txt':
            continue
        if os.path.isdir(os.path.join(project_source, fs_obj)):
            top_level_items.add(fs_obj)
        if fs_obj.endswith('.txt'):
            top_level_items.add(fs_obj[:-4])

    top_level_items = '/'+ r'[^\s]*|/'.join(top_level_items) + r'[^\s]*'

    re_string = r'(\\fB({0})\\fP)'.format(top_level_items).replace(r'-', r'\-')
    subst = conf.project.url + '/' + conf.project.tag + r'\2'

    regex_obj = (re.compile(re_string), subst)

    for manpage in expand_tree(os.path.join(conf.build.paths.projectroot,
                                            conf.build.paths.output,
                                            conf.git.branches.current,
                                            'man'), ['1', '5']):
        yield dict(target=manpage,
                   dependency=None,
                   job=manpage_url,
                   args=[regex_obj, manpage])


def _process_page(fn, output_fn, regex, builder='processor'):
    tmp_fn = n + '~'

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

    runner(jobs, pool=1)

def manpage_jobs():
    conf = get_conf()

    options_compat_re = [ (re.compile(r'\.\. option:: --'), r'.. setting:: ' ),
                          (re.compile(r'setting:: (\w+) .*'), r'setting:: \1'),
                          (re.compile(r':option:`--'), r':setting:`') ]


    jobs = [
        (
            os.path.join(conf.build.paths.includes, "manpage-options-auth.rst"),
            os.path.join(conf.build.paths.includes, 'manpage-options-auth-mongo.rst'),
            ( re.compile('fact-authentication-source-tool'),
              'fact-authentication-source-mongo' )
        ),
        (
            os.path.join(conf.build.paths.includes, 'manpage-options-ssl.rst'),
            os.path.join(conf.build.paths.includes, 'manpage-options-ssl-settings.rst'),
            options_compat_re
        ),
        (
            os.path.join(conf.build.paths.includes, 'manpage-options-audit.rst'),
            os.path.join(conf.build.paths.includes, 'manpage-options-audit-settings.rst'),
            options_compat_re
        )
    ]

    for input_fn, output_fn, regex in jobs:
        if os.path.exists(input_fn):
            yield {
                'target': output_fn,
                'dependency': input_fn,
                'job': _process_page,
                'args': [ input_fn, output_fn, regex, 'manpage' ],
              }

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
        if conf is None:
            conf = get_conf()

        if source_fn is None:
            source_fn = os.path.join(conf.build.paths.project.root,
                                     conf.build.paths.builddata,
                                     'processing.yaml')
        tasks = ingest_yaml(source_fn)
    elif not isinstance(tasks, collections.Iterable):
        abort('[ERROR]: cannot parse post processing specification.')

    def rjob(fn, regex, type):
        return {
                 'target': fn,
                 'dependency': None,
                 'job': _process_page,
                 'args': dict(fn=fn, output_fn=fn, regex=regex, builder=type)
               }

    for job in tasks:
        if not isinstance(job, dict):
            abort('[ERROR]: invalid replacement specification.')
        elif not 'file' in job and not 'transform' in job:
            abort('[ERROR]: replacement specification incomplete.')

        if 'type' not in job:
            job['type'] = 'processor'

        if isinstance(job['transform'], list):
            regex = [ ( re.compile(rs['regex'], rs['replace'] ) ) for rs  in job['transform'] ]
        else:
            regex = ( re.compile(job['transform']['regex'] ), job['transform']['replace'])

        if isinstance(job['file'], list):
            for fn in job['file']:
                yield rjob(fn, regex, job['type'])
        else:
            yield rjob(fn, regex, job['type'])
