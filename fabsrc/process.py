import os
import re
import subprocess

from fabric.api import task

from fabfile.utils.config import lazy_conf
from fabfile.utils.project import mms_should_migrate
from fabfile.utils.files import (create_link, copy_if_needed,
                                 decode_lines_from_file, encode_lines_to_file)
from fabfile.utils.serialization import ingest_yaml_list

from fabfile.utils.jobs.context_pools import ProcessPool, ThreadPool

#################### PDFs from Latex Produced by Sphinx  ####################

def _clean_sphinx_latex(fn, regexes):
    tex_lines = decode_lines_from_file(fn)

    for regex, subst in regexes:
        tex_lines = [ regex.sub(subst, tex) for tex in tex_lines ]

    encode_write_lines_to_file(fn, tex_lines)

    print('[pdf]: processed Sphinx latex format for {0}'.format(fn))

def _render_tex_into_pdf(fn, path):
    pdflatex = 'TEXINPUTS=".:{0}:" pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False

    print('[pdf]: completed pdf rendering stage 1 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call("makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, os.path.basename(fn)[:-4]), shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
    print('[pdf]: completed pdf rendering stage 2 of 4 (indexing) for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessError:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    print('[pdf]: completed pdf rendering stage 3 of 4 for: {0}'.format(fn))

    try:
        with open(os.devnull, 'w') as f:
            subprocess.check_call(pdflatex, shell=True, stdout=f, stderr=f)
    except subprocess.CalledProcessErro:
        print('[ERROR]: {0} file has errors, regenerate and try again'.format(fn))
        return False
    print('[pdf]: completed pdf rendering stage 4 of 4 for: {0}'.format(fn))

    print('[pdf]: rendered {0}.{1}'.format(os.path.basename(fn), 'pdf'))

@task
def pdfs():
    "Processes '.tex' files and runs 'pdflatex' to generate all PDFs."

    pdf_worker()

def pdf_worker(target=None, conf=None):
    conf = lazy_conf(conf)

    if target is None:
        target = 'latex'

    force = False
    with ProcessPool() as p:
        res = []
        for it, queue in enumerate(pdf_jobs(target, conf)):
            res.extend(p.runner(queue))

            print("[pdf]: completed {0} pdf jobs, in stage {1}".format(len(queue), it))

def pdf_jobs(target, conf):
    pdfs = ingest_yaml_list(os.path.join(conf.paths.builddata, 'pdfs.yaml'))
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

        latex_dir = os.path.join(conf.paths.branch_output, target)

        if 'edition' in i:
            deploy_path = os.path.join(conf.paths.public, i['edition'])

            target_split = target.split('-')

            if len(target_split) > 1:
                if target_split[1] != i['edition']:
                    continue

            if i['edition'] == 'hosted':
                deploy_path = os.path.join(deploy_path,  conf.git.branches.current)
            else:
                deploy_fn = tagged_name + '.pdf'
                link_name = deploy_fn
        else:
            deploy_path = conf.paths.branch_staging

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

        if conf.project.name == 'mms' and mms_should_migrate(target, conf) is False:
            pass
        else:
            queue[3].append(dict(dependency=i['pdf'],
                                 target=i['deployed'],
                                 job=copy_if_needed,
                                 args=(i['pdf'], i['deployed'], 'pdf')))

            if i['link'] != i['deployed']:
                queue[4].append(dict(dependency=i['deployed'],
                                     target=i['link'],
                                     job=create_link,
                                     args=(deploy_fn, i['link'])))

    return queue
