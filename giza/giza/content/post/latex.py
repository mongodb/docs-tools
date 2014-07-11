import os
import re
import subprocess
import logging

logger = logging.getLogger('giza.content.post.latex')

from giza.command import command

from giza.files import (create_link, copy_if_needed,
                                 decode_lines_from_file, encode_lines_to_file)
from giza.serialization import ingest_yaml_list
from giza.transformation import munge_page

#################### PDFs from Latex Produced by Sphinx  ####################

def _clean_sphinx_latex(fn, regexes):
    munge_page(fn, regexes, tag='pdf')

def _render_tex_into_pdf(fn, path):
    pdflatex = 'TEXINPUTS=".:{0}:" pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)

    base_fn = os.path.basename(fn)
    cmds = [ pdflatex,
             "makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, base_fn[:-4]),
             pdflatex,
             pdflatex ]

    for idx, cmd in enumerate(cmds):
        r = command(command=cmd, ignore=True)

        if r.succeeded is True:
            logger.info('pdf completed rendering stage {0} of {1} successfully.'.format(idx, len(cmds)))
        else:
            if idx <= 1:
                logger.warning('pdf build encountered error early on {0}, continuing cautiously.'.format(base_fn))
                continue
            else:
                logger.error('pdf build encountered error running pdflatex, investigate on {0}. terminating'.format(base_fn))
                return False

def pdf_tasks(target, conf, app):
    if 'pdfs' not in conf.system.files.data:
        return

    app.pool = 'thread'

    tex_regexes = [ ( re.compile(r'(index|bfcode)\{(.*)--(.*)\}'),
                      r'\1\{\2-\{-\}\3\}'),
                    ( re.compile(r'\\PYGZsq{}'), "'"),
                    ( re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv)'),
                      r'\code{' + conf.project.url + r'/' + conf.project.tag) ]

    clean_app = app.add('app')
    cache_app = app.add('app')
    render_app = app.add('app')
    migrate_app = app.add('app')
    link_app = app.add('app')

    for i in conf.system.files.data.pdfs:
        tagged_name = i['output'][:-4] + '-' + i['tag']
        deploy_fn = tagged_name + '-' + conf.git.branches.current + '.pdf'
        link_name = deploy_fn.replace('-' + conf.git.branches.current, '')

        latex_dir = os.path.join(conf.paths.branch_output, target)
        deploy_path = conf.paths.public_site_output

        i['source'] = os.path.join(latex_dir, i['output'])
        i['processed'] = os.path.join(latex_dir, tagged_name + '.tex')
        i['pdf'] = os.path.join(latex_dir, tagged_name + '.pdf')
        i['deployed'] = os.path.join(deploy_path, deploy_fn)
        i['link'] = os.path.join(deploy_path, link_name)
        i['path'] = latex_dir

        clean_task = clean_app.add('task')
        clean_task.target = i['source']
        clean_task.job = _clean_sphinx_latex
        clean_task.args = (i['source'], tex_regexes)

        cache_task = cache_app.add('task')
        cache_task.dependency = i['source']
        cache_task.target = i['processed']
        cache_task.job = copy_if_needed
        cache_task.args = (i['source'], i['processed'], 'pdf')

        render_task = render_app.add('task')
        render_task.dependency = i['processed']
        render_task.target = i['pdf']
        render_task.job = _render_tex_into_pdf
        render_task.args = (i['processed'], i['path'])

        migrate_task = migrate_app.add('task')
        migrate_task.dependency = i['pdf']
        migrate_task.target = i['deployed']
        migrate_task.job = copy_if_needed
        migrate_task.args = (i['pdf'], i['deployed'], 'pdf')

        if i['link'] != i['deployed']:
            link_task = link_app.add('task')
            link_task.dependency = i['deployed']
            link_task.target = i['link']
            link_task.job = create_link
            link_task.args = (deploy_fn, i['link'])
