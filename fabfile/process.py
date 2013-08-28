import json
import re
import os
import shutil

from utils import md5_file, symlink, expand_tree, dot_concat, ingest_yaml_list
from make import check_dependency, check_three_way_dependency
from docs_meta import output_yaml, get_manual_path, get_conf
from fabric.api import task, env, abort, puts, local
import subprocess
from generate import runner

env.input_file = None
env.output_file = None

@task
def input(fn):
    env.input_file = fn

@task
def output(fn):
    env.output_file = fn

########## Process Sphinx Json Output ##########

@task
def json_output():
    if env.input_file is None or env.output_file is None:
        all_json_output()
    else:
        process_json_file(env.input_file, env.output_file)

def all_json_output():
    conf = get_conf()

    count = runner(json_output_jobs())

    puts('[json]: processed {0} json files.'.format(str(count)))

    list_file = os.path.join(conf.build.paths.branch_output, 'json-file-list')
    public_list_file = os.path.join(conf.build.paths.public,
                                  conf.git.branches.current,
                                  'json',
                                  '.file_list')

    cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {src} {dst}'
    json_dst = os.path.join(conf.build.paths['branch-staging'], 'json')

    if not os.path.exists(json_dst):
        os.makedirs(json_dst)

    local(cmd.format(src=os.path.join(conf.build.paths['branch-output'], 'json'),
                     dst=json_dst))
    _copy_if_needed(list_file, public_list_file)

    puts('[json]: deployed json files to local staging.')

def json_output_jobs():
    conf = get_conf()

    outputs = []
    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>
        path = os.path.join(conf.build.paths.output, conf.git.branches.current,
                            'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])
        fjson = dot_concat(path, 'fjson')
        json = dot_concat(path, 'json')

        yield dict(target=json,
                   dependency=fjson,
                   job=process_json_file,
                   args=(fjson, json))

        outputs.append(json)

    list_file = os.path.join(conf.build.paths.branch_output, 'json-file-list')

    yield dict(target=list_file,
               dependency=None,
               job=generate_list_file,
               args=(outputs, list_file))

def generate_list_file(outputs, path):
    dirname = os.path.dirname(path)

    if get_conf().git.remote.upstream.endswith('ecosystem'):
        url = 'http://docs.mongodb.org/ecosystem'
    else:
        url = '/'.join(['http://docs.mongodb.org', get_manual_path()])

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(path, 'w') as f:
        for fn in outputs:
            f.write( '/'.join([ url, 'json', fn.split('/', 3)[3:][0]]))
            f.write('\n')

    puts('[json]: rebuilt inventory of json output.')

def process_json_file(input_fn, output_fn):
    with open(input_fn, 'r') as f:
        document = f.read()

    doc = json.loads(document)

    if 'body' in doc:
        text = doc['body'].encode('ascii', 'ignore')

        text = re.sub(r'<a class=\"headerlink\"', '.<a', text)
        text = re.sub('<[^>]*>', '', text)
        text = re.sub('&#8220;', '"', text)
        text = re.sub('&#8221;', '"', text)
        text = re.sub('&#8216;', "'", text)
        text = re.sub('&#8217;', "'", text)
        text = re.sub(r'&#\d{4};', '', text)
        text = re.sub('&nbsp;', '', text)

        doc['text'] = ' '.join(text.split('\n')).strip()

    if 'title' in doc:
        title = doc['title'].encode('ascii', 'ignore')
        title = re.sub('<[^>]*>', '', title)

        doc['title'] = title

    url = [ 'http://docs.mongodb.org', get_manual_path() ]
    url.extend(input_fn.rsplit('.', 1)[0].split(os.path.sep)[3:])
    doc['url'] = '/'.join(url)

    with open(output_fn, 'w') as f:
        f.write(json.dumps(doc))

    puts('[json]: generated a processed json file: ' + output_fn)

########## Update Dependencies ##########

def update_dependency(fn):
    if os.path.exists(fn):
        os.utime(fn, None)
        puts('[dependency]: updated timestamp of {0} because its included files changed'.format(fn))

def fix_include_path(inc, fn, source):
    if inc.startswith('/'):
        return ''.join([source + inc])
    else:
        return os.path.join(os.path.dirname(os.path.abspath(fn)), fn)

def check_deps(file, pattern):
    includes = []
    try:
        with open(file, 'r') as f:
            for line in f:
                r = pattern.findall(line)
                if r:
                    includes.append(fix_include_path(r[0], file, 'source'))
        if len(includes) >= 1:
            if check_dependency(file, includes):
                update_dependency(file)
    except IOError:
        pass

@task
def refresh_dependencies():
    count = runner(composite_jobs())
    puts('[dependency]: updated timestamps of {0} files'.format(count))

def composite_jobs():
    files = expand_tree('source', 'txt')
    inc_pattern = re.compile(r'\.\. include:: (.*\.(?:txt|rst))')

    for fn in files:
        yield {
                'target': fn,
                'dependency': None,
                'job': check_deps,
                'args': [ fn, inc_pattern ]
              }

########## Simple Tasks ##########

@task
def meta():
    output_yaml(env.output_file)

@task
def touch(fn, times=None):
    if os.path.exists(fn):
        os.utime(fn, times)

########## Main Output Processing Targets ##########

@task
def manpage_url():
    if env.input_file is None:
        abort('[man]: you must specify input and output files.')

    project_source = 'source'

    top_level_items = set()
    for fs_obj in os.listdir(project_source):
        if fs_obj.startswith('.static') or fs_obj == 'index.txt':
            continue
        if os.path.isdir(os.path.join(project_source, fs_obj)):
            top_level_items.add(fs_obj)
        if fs_obj.endswith('.txt'):
            top_level_items.add(fs_obj[:-4])

    top_level_items = '/' + '.*|/'.join(top_level_items)
    re_string = '(\\\\fB({0}.*)\\\\fP)'.format(top_level_items)

    with open(env.input_file, 'r') as f:
        manpage = f.read()

    manpage = re.sub(re_string, "http://docs.mongodb.org/manual\\2", manpage)

    with open(env.input_file, 'w') as f:
        f.write(manpage)

    puts("[{0}]: fixed urls in {1}".format('man', env.input_file))

@task
def copy_if_needed(source_file=None, target_file=None, name='build'):
    _copy_if_needed(source_file, target_file, name)

class InvalidPath(Exception): pass

def _copy_if_needed(source_file=None, target_file=None, name='build'):
    if source_file is None:
        source_file = env.input_file

    if target_file is None:
        target_file = env.output_file

    if os.path.isfile(source_file) is False:
        puts("[{0}]: Input file '{1}' does not exist.".format(name, source_file))
        raise InvalidPath
    elif os.path.isfile(target_file) is False:
        if not os.path.exists(os.path.dirname(target_file)):
            os.makedirs(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

        if name is not None:
            puts('[{0}]: created "{1}" which did not exist.'.format(name, source_file))
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

@task
def manual_single_html():
    if env.input_file is None or env.output_file is None:
        abort('[single]: you must specify input and output files.')

    with open(env.input_file, 'r') as f:
        text = f.read()

    text = re.sub('href="contents.html', 'href="index.html', text)
    text = re.sub('name="robots" content="index"', 'name="robots" content="noindex"', text)
    text = re.sub('(href=")genindex.html', '\1../genindex/', text)

    with open(env.output_file, 'w') as f:
        f.write(text)

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
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    puts('[pdf]: completed pdf rendering stage 4 of 4 for: {0}'.format(fn))

    puts('[pdf]: rendered {0}.{1}'.format(os.path.basename(fn), 'pdf'))

@task
def pdfs():
    for queue in pdf_jobs():
        runner(queue)

def pdf_jobs():
    conf = get_conf()

    pdfs = ingest_yaml_list(os.path.join(conf.build.paths.builddata, 'pdfs.yaml'))
    tex_regexes = [(re.compile(r'(index|bfcode)\{(.*)--(.*)\}'), r'\1\{\2-\{-\}\3\}'),
                   (re.compile(r'\\PYGZsq{}'), "'"),
                   (re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv)'), r'\code{' + conf.project.url + r'/' + conf.project.tag) ]

    # this is temporary
    queue = ( [], [], [], [], [] )
    pdfs.sort()

    for i in pdfs:
        tagged_name = i['output'][:-4] + '-' + i['tag']
        deploy_fn = tagged_name + '-' + conf.git.branches.current + '.pdf'
        link_name = deploy_fn.replace('-' + conf.git.branches.current, '')

        if 'edition' in i:
            deploy_path = os.path.join(conf.build.paths.public, i['edition'])
            if i['edition'] == 'hosted':
                deploy_path = os.path.join(deploy_path,  conf.git.branches.current)
                latex_dir = os.path.join(conf.build.paths.output, i['edition'], conf.git.branches.current, 'latex')
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
        i['fn'] = deploy_fn
        i['path'] = latex_dir

        # these appends will become yields, once runner() can be dependency
        # aware.
        queue[0].append(dict(dependency=None,
                             target=i['source'],
                             job=_clean_sphinx_latex,
                             args=(i['source'], tex_regexes)))

        queue[1].append(dict(dependency=i['source'],
                             target=i['processed'],
                             job=_copy_if_needed,
                             args=(i['source'], i['processed'], 'pdf')))

        queue[2].append(dict(dependency=i['processed'],
                             target=i['pdf'],
                             job=_render_tex_into_pdf,
                             args=(i['processed'], i['path'])))

        queue[3].append(dict(dependency=i['pdf'],
                             target=i['deployed'],
                             job=_copy_if_needed,
                             args=(i['pdf'], i['deployed'], 'pdf')))

        if i['link'] != i['deployed']:
            queue[4].append(dict(dependency=i['deployed'],
                                 target=i['link'],
                                 job=_create_link,
                                 args=(i['link'], i['fn'])))

    return queue

#################### Error Page Processing ####################

# this is called directly from the sphinx generation function in sphinx.py.

def _munge_page(fn, regex):
    with open(fn, 'r') as f:
        page = f.read()

    page = regex[0].sub(regex[1], page)

    with open(fn, 'w') as f:
        f.write(page)

    puts('[error-pages]: processed {0}'.format(fn))

def error_pages():
    conf = get_conf()

    error_conf = os.path.join(conf.build.paths.builddata, 'errors.yaml')

    if not os.path.exists(error_conf):
        return None
    else:
        error_pages = ingest_yaml_list(error_conf)

        sub = (re.compile(r'\.\./\.\./'), conf.project.url + conf.project.tag + '/')

        for error in error_pages:
            page = os.path.join(conf.build.paths.projectroot, conf.build.paths['branch-output'], 'dirhtml', 'meta', error, 'index.html')
            _munge_page(page, sub)

        puts('[error-pages]: rendered {0} error pages'.format(len(error_pages)))
