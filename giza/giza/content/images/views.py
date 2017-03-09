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

import logging
import os.path
import docutils.core
from rstcloth.rstcloth import RstCloth

logger = logging.getLogger('giza.content.images.views')


def generate_image_pages(image, conf):
    r = RstCloth()

    dir = image.dir
    name = image.name
    alt = image.alt
    output = image.outputs
    image = os.path.sep.join([dir, name])

    for img_output in output:
        width = str(img_output.width) + 'px'
        build_type = img_output.build_type

        r.newline()

        if 'tag' in img_output:
            tag = ''.join(['-', img_output.tag, '.', build_type])
        else:
            tag = '.' + build_type

        options = [('alt', alt), ('align', 'center'), ('figwidth', width)]

        if 'scale' in img_output:
            options.append(('scale', img_output.scale))
        if 'target' in img_output:
            options.append(('target', (img_output.target)))

        if img_output.type == 'target':
            continue
        elif img_output.type == 'print':
            r.directive('only', 'latex and not offset', wrap=False)
            r.newline()

            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3)
        elif img_output.type == 'offset':
            tex_figure = [
                r'\begin{center}',
                ''.join([r'\includegraphics[width=', width,
                         ']{', name, tag, '}']),
                r'\end{center}'
            ]

            r.directive('only', 'latex and offset', wrap=False)
            r.newline()
            r.directive('raw', 'latex', content=tex_figure, indent=3)
        else:
            r.directive('only', 'website and slides', wrap=False)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3)

            r.newline()

            r.directive('only', 'website and html', wrap=False)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3)

            r.newline()

            if img_output.width > 740:
                options[2] = ('figwidth', '740px')

            r.directive('only', 'website and not (html or slides)', wrap=False)
            r.newline()
            img_str = ''.join(['<div class="figure align-center" style="max-width:{5};">',
                               '<img src="{0}/{1}/_images/{2}{3}" alt="{4}">', '</img>',
                               '{6}</div>'])
            alt_html = docutils.core.publish_parts(alt, writer_name='html')['body'].strip()
            r.directive(name='raw', arg='html',
                        content=img_str.format(conf.project.url,
                                               conf.git.branches.current, name, tag, alt,
                                               width, alt_html),
                        indent=3)

        r.newline()

    image_rst_file_path = os.path.join(conf.paths.projectroot, image + '.rst')
    r.write(image_rst_file_path)
    logger.info('generated include file {0}.rst'.format(image))
