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

import sys
import os.path
import logging

logger = logging.getLogger('giza.content.images')

from docutils.core import publish_parts
from rstcloth.rstcloth import RstCloth

from giza.tools.command import command
from giza.tools.files import verbose_remove
from giza.tools.serialization import ingest_yaml_list
from giza.tools.strings import dot_concat, hyph_concat

## Internal Supporting Methods

def generate_image_pages(dir, name, alt, output, conf):
    r = RstCloth()

    image = '/'.join([dir, name])
    b = name

    for img_output in output:
        img_output['width'] = str(img_output['width']) + 'px'

        if img_output['type'] == 'offset':
            build_type = 'eps'
        else:
            build_type = 'png'

        r.newline()

        if 'tag' in img_output:
            tag = ''.join(['-', img_output['tag'], '.', build_type ])
        else:
            tag = '.' + build_type

        options = [('alt', alt), ('align', 'center'), ('figwidth', img_output['width'])]

        if 'scale' in img_output:
            options.append(('scale', img_output['scale']))
        if img_output['type'] in 'print':
            r.directive('only', 'latex and not offset', wrap=False, block=b)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3,
                        content=alt,
                        block=b)
            r.newline()
        elif img_output['type'] == 'offset':
            r.directive('only', 'latex and offset', wrap=False, block=b)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3,
                        content=alt,
                        block=b)
        else:
            alt_html = publish_parts(alt, writer_name='html')['body'].strip()
            img_tags = ['<div class="figure align-center" style="max-width:{5};">',
                        '<img src="{0}/{1}/_images/{2}{3}" alt="{4}">', '</img>',
                        '{6}</div>' ]
            img_str = ''.join(img_tags)


            r.directive('only', 'website and not (html or slides)', wrap=False, block=b)
            r.newline()
            r.directive(name='raw', arg='html',
                        content=img_str.format(conf.project.url,
                                               conf.git.branches.current, name, tag, alt,
                                               img_output['width'], alt_html),
                        indent=3,
                        block=b)

            r.newline(count=2)

            if img_output['width'] > 600:
                options[2] = ('figwidth', 600)

            r.directive('only', 'website and (html or slides)', wrap=False, block=b)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3,
                        content=alt,
                        block=b)


        r.newline()

    image_rst_file_path = os.path.join(conf.paths.projectroot, image + '.rst')
    r.write(image_rst_file_path)
    logger.info('generated include file {0}.rst'.format(image))

def _get_inkscape_cmd():
    if sys.platform in ['linux', 'linux2']:
        return '/usr/bin/inkscape'
    elif sys.platform == 'darwin':
        inkscape = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape'
        if os.path.exists(inkscape):
            return inkscape

    return 'inkscape'

def _generate_images(cmd, dpi, width, target, source):
    full_cmd = cmd.format(cmd=_get_inkscape_cmd(),
                          dpi=dpi,
                          width=width,
                          target=target,
                          source=source)
    command(full_cmd)

    logger.debug(full_cmd)

    logger.info('generated image file {0}'.format(target))

def get_images_metadata_file(conf):
    base = None
    for fn in conf.system.files.paths:
        if isinstance(fn, dict):
            if 'images' in fn:
                base = fn['images']
                break
        else:
            if fn.startswith('images'):
                base = fn
                break

    if base is None:
        return None
    elif base.startswith('/'):
        base = base[1:]
        return os.path.join(conf.paths.projectroot, base)
    else:
        return os.path.join(conf.paths.projectroot, conf.paths.builddata, base)

def image_tasks(conf, app):
    meta_file = get_images_metadata_file(conf)

    if 'images' not in conf.system.files.data:
        logger.info('no images to generate')
        return

    if isinstance(conf.system.files.data.images, list):
        images = conf.system.files.data.images
    else:
        images = [ conf.system.files.data.images ]

    image_dir = conf.paths.branch_images

    for image in images:
        image['dir'] = image_dir
        image['conf'] = conf

        source_base = os.path.join(conf.paths.projectroot, image['dir'], image['name'])
        source_file = dot_concat(source_base, 'svg')
        source_core = os.path.join(conf.paths.projectroot, conf.paths.images, image['name'] + '.svg' )
        rst_file = dot_concat(source_base, 'rst')

        if not os.path.isfile(source_file):
            logger.error('"{0}" does not exist'.format(source_core))
            continue

        t = app.add('task')
        t.conf = conf
        t.job = generate_image_pages
        t.args = image # as kwargs
        t.description = "generating rst include file {0} for {1}".format(rst_file, source_core)
        t.target = rst_file
        t.dependency = meta_file
        logger.debug('adding task for image rst file: {0}'.format(rst_file))

        for output in image['output']:
            if output['type'] == 'offset':
                build_type = 'eps'
            else:
                build_type = 'png'

            if 'tag' in output:
                tag = '-' + output['tag']
            else:
                tag = ''

            target_img = ''.join([source_base, tag, '.', build_type])

            if build_type == 'png':
                inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 0.0 -e >/dev/null {target} {source}'
            elif build_type == 'eps':
                inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 1.0 -E >/dev/null {target} {source}'

            t = app.add('task')
            t.conf = conf
            t.job = _generate_images
            t.args = [ inkscape_cmd, output['dpi'], output['width'], target_img, source_file ]
            t.target = target_img
            t.dependency = [ meta_file, source_core ]
            t.description = 'generating image file {0} from {1}'.format(target_img, source_core)
            logger.debug('adding image creation job for {0}'.format(target_img))

def image_clean(conf, app):
    if 'images' not in conf.system.files.data:
        logger.info('no images to clean')
        return

    for image in conf.system.files.data.images:
        source_base = os.path.join(conf.paths.projectroot, conf.paths.images, image['name'])

        rm_rst = app.add('task')
        rm_rst.job = verbose_remove
        rm_rst.args = dot_concat(source_base, 'rst')

        for output in image['output']:
            rm_tag_image = app.add('task')
            rm_tag_image.job = verbose_remove
            if 'tag' in output:
                rm_tag_image.args = dot_concat(hyph_concat(source_base, output['tag']), 'png')
            else:
                rm_tag_image.args = dot_concat(source_base, 'png')
