import json
import re
import os
import shutil

from utils import md5_file, symlink, expand_tree, dot_concat, ingest_yaml_list
from make import check_dependency, check_three_way_dependency
from docs_meta import output_yaml, get_manual_path, get_conf, get_branch_output_path
from fabric.api import task, env, abort, puts, local
from multiprocessing import Pool, Process

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
    p = Pool()
    conf = get_conf()

    outputs = []
    count = 0
    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>
        path = os.path.join(conf.build.paths.output, conf.git.branches.current,
                            'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])
        fjson = dot_concat(path, 'fjson')
        json = dot_concat(path, 'json')

        if check_three_way_dependency(json, fn, fjson):
            p.apply_async(process_json_file, args=(fjson, json))
            count += 1

        outputs.append(json)

    list_file = os.path.join(get_branch_output_path(), 'json-file-list')
    public_list_file = os.path.join(conf.build.paths.public,
                                  conf.git.branches.current,
                                  'json',
                                  '.file_list')

    p.apply_async(generate_list_file, args=(outputs, list_file))


    p.close()
    p.join()

    puts('[json]: processed {0} json files.'.format(str(count)))

    cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {src} {dst}'
    json_dst = os.path.join(conf.build.paths['branch-staging'], 'json')

    if not os.path.exists(json_dst):
        os.makedirs(json_dst)

    local(cmd.format(src=os.path.join(conf.build.paths['branch-output'], 'json'),
                     dst=json_dst))
    _copy_if_needed(list_file, public_list_file)

    puts('[json]: deployed json files to local staging.')

@task
def test():
    conf = get_conf()

    import json
    print json.dumps(conf.build.paths, indent=3)

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
    files = expand_tree('source', 'txt')
    inc_pattern = re.compile(r'\.\. include:: (.*\.(?:txt|rst))')

    dep_info = []
    p = Pool()

    for fn in files:
        p.apply_async(check_deps, kwds=dict(file=fn, pattern=inc_pattern))

    p.close()
    p.join()


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

def _copy_if_needed(source_file=None, target_file=None, name='build'):
    if source_file is None:
        source_file = env.input_file

    if target_file is None:
        target_file = env.output_file

    if os.path.isfile(source_file) is False:
        abort("[{0}]: Input file '{1}' does not exist.".format(name, source_file))
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
                puts('[{0}]: "{1}" changed.'.format(name, source_file))

@task
def create_link():
    _create_link(env.input_file, env.output_file)

def _create_link(input_fn, output_fn):
    out_dirname = os.path.dirname(input_fn)
    if out_dirname != '' and not os.path.exists(out_dirname):
        os.makedirs(out_dirname)

    if os.path.islink(output_fn):
        os.remove(output_fn)
    elif os.path.isdir(output_fn):
        abort('[{0}]: {1} exists and is a directory'.format('link', output_fn))
    elif os.path.exists(output_fn):
        abort('[{0}]: could not create a symlink at {1}.'.format('link', output_fn))

    symlink(output_fn, input_fn)
    puts('[{0}] created symbolic link pointing to "{1}" named "{2}"'.format('symlink', input_fn, output_fn))

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

env.verbose = False

def _render_tex_into_pdf(fn, path):
    pdflatex = 'TEXINPUTS=".:{0}:" pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)

    if env.verbose:
        capture = False
    else:
        capture = True

    local(pdflatex, capture=capture)
    puts('[pdf]: completed pdf rendering stage 1 of 4 for: {0}'.format(fn))

    local("makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, os.path.basename(fn)[:-4]), capture=capture)
    puts('[pdf]: completed pdf rendering stage 2 of 4 (indexing) for: {0}'.format(fn))

    local(pdflatex, capture=capture)
    puts('[pdf]: completed pdf rendering stage 3 of 4 for: {0}'.format(fn))

    local(pdflatex, capture=capture)
    puts('[pdf]: completed pdf rendering stage 4 of 4 for: {0}'.format(fn))

    puts('[pdf]: rendered pdf for {0}'.format(fn))


def _sanitize_tex(files):
    conf = get_conf()
    regexes = [(re.compile(r'(index|bfcode)\{(.*)--(.*)\}'), r'\1\{\2-\{-\}\3\}'),
               (re.compile(r'\\code\{/(?!.*{}/|etc)'), r'\code{' + conf.project.url + conf.project.tag) ]

    p = Pool()

    count = 0
    for fn in files:
        # _clean_sphinx_latex(fn, regexes)
        p.apply_async(_clean_sphinx_latex, args=(fn, regexes))
        count += 1

    p.close()
    p.join()

    puts('[pdf]: sanitized sphinx tex output in {0} files'.format(count))

def _generate_pdfs(targets):
    conf = get_conf()

    p = Pool(4)

    count = 0
    for tex, pdf, path in targets:
        if check_dependency(pdf, tex):
            # _render_tex_into_pdf(tex, path)
            p.apply_async(_render_tex_into_pdf, args=(tex, path))
            count += 1

    p.close()
    p.join()

    puts('[pdf]: rendered {0} tex files into pdfs.'.format(count))

def _multi_copy_if_needed(target_pairs):
    p = Pool(4)

    for source, target, builder in target_pairs:
        # _copy_if_needed(source, target, builder)
        p.apply_async(_copy_if_needed, args=(source, target, builder))

    p.close()
    p.join()

def _multi_create_link(link_pairs):
    p = Pool(2)

    for link, source in link_pairs:
        _create_link(source, link)

    p.close()
    p.join()

@task
def pdfs():
    conf = get_conf()

    pdfs = ingest_yaml_list(os.path.join(conf.build.paths.builddata, 'pdfs.yaml'))

    sources = []
    tex_pairs = []
    pdf_pairs = []
    targets = []
    pdf_links = []

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

        sources.append(i['source'])
        tex_pairs.append([i['source'], i['processed'], 'pdf'])
        targets.append([i['processed'], i['pdf'], latex_dir])
        pdf_pairs.append([i['pdf'], i['deployed'], 'pdf'])

        if i['link'] != i['deployed']:
            pdf_links.append((i['link'], i['deployed']))

    _sanitize_tex(sources)
    _multi_copy_if_needed(tex_pairs)
    _generate_pdfs(targets)
    _multi_copy_if_needed(pdf_pairs)

    if len(pdf_links) > 0:
        _multi_create_link(pdf_links)
