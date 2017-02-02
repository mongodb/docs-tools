# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Post-processes Sphinx's latex output and generate PDFs from these ``tex`` files.
"""

import logging
import os
import re
import subprocess
import shlex

import giza.libgiza.task

from giza.content.helper import edition_check
from giza.tools.transformation import process_page_task
from giza.tools.files import create_link, copy_if_needed

logger = logging.getLogger('giza.content.post.latex')

# PDFs from Latex Produced by Sphinx


def _render_tex_into_pdf(fn, deployed_path, path, output_format="pdf"):
    """
    Runs ``pdflatex`` operations, can generate ``dvi`` and ``pdf``. Runs
    pdflatex multiple times to correctly index and cross reference the PDF.
    """

    inputs_path = ".:{0}:".format(path)
    os.environ['TEXINPUTS'] = inputs_path

    if output_format == 'dvi':
        cmd = 'pdflatex --output-format dvi --interaction batchmode --output-directory {0} {1}'
        pdflatex = cmd.format(path, fn)
    elif output_format == 'pdf':
        pdflatex = 'pdflatex --interaction batchmode --output-directory {0} {1}'.format(path, fn)
    else:
        logger.error('not rendering pdf because {0} is not an output format'.format(output_format))
        return

    base_fn = os.path.basename(fn)
    cmds = [pdflatex,
            "makeindex -s {0}/python.ist {0}/{1}.idx ".format(path, base_fn[:-4]),
            pdflatex,
            pdflatex]

    if output_format == 'dvi':
        cmds.append("dvipdf {0}.dvi".format(base_fn[:-4]))

    with open(os.devnull, 'w') as null:
        for idx, cmd in enumerate(cmds):
            ret = subprocess.call(args=shlex.split(cmd),
                                  cwd=path,
                                  stdout=null,
                                  stderr=null)
            if ret == 0:
                m = 'pdf completed rendering stage {0} of {1} successfully ({2}, {3}).'
                logger.info(m.format(idx + 1, len(cmds), base_fn, ret))
                continue
            else:
                if idx <= 1:
                    m = 'pdf build encountered error early on {0}, continuing cautiously.'
                    logger.warning(m.format(base_fn))
                    continue
                else:
                    m = 'pdf build encountered error running pdflatex, investigate {0}. terminating'
                    logger.error(m.format(base_fn))
                    logger.error(' '.join(['TEXINPUTS={0} '.format(inputs_path),
                                           cmd.replace('--interaction batchmode', '')]))
                    return False

    pdf_fn = os.path.splitext(fn)[0] + '.pdf'
    copy_if_needed(pdf_fn, deployed_path, 'pdf')


def pdf_tasks(sconf, conf):
    """Returns a list of Tasks() to generate all PDFs."""

    tasks = []
    target = sconf.builder
    if 'pdfs' not in conf.system.files.data:
        return []

    # a list of tuples in (compileRegex, substitution) format.
    tex_regexes = [
        (re.compile(r'(index|bfcode)\{(.*)--(.*)\}'),
         r'\1\{\2-\{-\}\3\}'),
        (re.compile(r'\\PYGZsq{}'), "'"),
        (re.compile(r'\\code\{/(?!.*{}/|etc|usr|data|var|srv|data|bin|dev|opt|proc|24|private)'),
         r'\code{' + conf.project.url + r'/' + conf.project.tag + r'/')]

    # the path that sphinx writes tex files to are are different for editions.
    if 'edition' in conf.project and conf.project.edition != conf.project.name:
        latex_dir = os.path.join(conf.paths.projectroot,
                                 conf.paths.branch_output,
                                 '-'.join((target, conf.project.edition)))
    else:
        latex_dir = os.path.join(conf.paths.projectroot, conf.paths.branch_output, target)

    deploy_path = os.path.join(conf.paths.projectroot, conf.paths.public_site_output)

    # special case operations on "offset pdfs", which use EPS images.
    if 'tags' in sconf and "offset" in sconf.tags:
        output_format = "dvi"
        sty_file = os.path.join(latex_dir, 'sphinx.sty')
        t = process_page_task(fn=sty_file,
                              output_fn=sty_file,
                              regex=(re.compile(r'\\usepackage\[pdftex\]\{graphicx\}'),
                                     r'\usepackage{graphicx}'),
                              builder='sphinx-latex',
                              copy='ifNeeded')
        tasks.append(t)
    else:
        output_format = "pdf"

    for i in conf.system.files.data.pdfs:
        if edition_check(i, conf) is False:
            continue

        # compatibility shim for new/old images
        i = i.dict()

        if len(i['tag']) == 0:
            tagged_name = i['output'][:-4]
        else:
            tagged_name = i['output'][:-4] + '-' + i['tag']

        deploy_fn = tagged_name + '-' + conf.git.branches.current + '.pdf'
        link_name = deploy_fn.replace('-' + conf.git.branches.current, '')

        i['source'] = os.path.join(latex_dir, i['output'])
        i['processed'] = os.path.join(latex_dir, tagged_name + '.tex')
        i['pdf'] = os.path.join(latex_dir, tagged_name + '.pdf')
        i['deployed'] = os.path.join(deploy_path, deploy_fn)
        i['link'] = os.path.join(deploy_path, link_name)
        i['path'] = latex_dir

        # add the processing task
        t = process_page_task(fn=i['source'],
                              output_fn=i['processed'],
                              regex=tex_regexes,
                              builder='tex-munge',
                              copy='ifNeeded')
        tasks.append(t)

        # add task for changing TEX to PDF. (this also copies the pdf to the deployed path).
        render_task = giza.libgiza.task.Task(job=_render_tex_into_pdf,
                                             args=(i['processed'], i['deployed'],
                                                   i['path'], output_format),
                                             target=i['pdf'],
                                             dependency=None)  # i['processed']
        t.finalizers.append(render_task)

        # if needed create links.
        if i['link'] != i['deployed']:
            link_task = giza.libgiza.task.Task(job=create_link,
                                               args=(deploy_fn, i['link']),
                                               target=i['link'],
                                               dependency=i['deployed'])
            render_task.finalizers.append(link_task)

    return tasks
