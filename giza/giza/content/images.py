import sys
import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from docutils.core import publish_parts
from rstcloth.rstcloth import RstCloth

from giza.command import command

from giza.tools.strings import dot_concat
from giza.tools.serialization import ingest_yaml_list

## Internal Supporting Methods

def generate_image_pages(dir, name, alt, output, conf):
    r = RstCloth()

    image = '/'.join([dir, name])
    b = name

    for img_output in output:
        img_output['width'] = str(img_output['width']) + 'px'

        r.newline()

        if 'tag' in img_output:
            tag = '-' + img_output['tag'] + '.png'
        else:
            tag = '.png'

        options = [('alt', alt), ('align', 'center'), ('figwidth', img_output['width'])]

        if 'scale' in img_output:
            options.append(('scale', img_output['scale']))

        if img_output['type'] == 'print':
            r.directive('only', 'latex', wrap=False, block=b)
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

            r.directive('only', 'website and not html', wrap=False, block=b)
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

            r.directive('only', 'website and html', wrap=False, block=b)
            r.newline()
            r.directive(name='figure',
                        arg='/images/{0}{1}'.format(name, tag),
                        fields=options,
                        indent=3,
                        content=alt,
                        block=b)


        r.newline(block=b)

    r.write(image + '.rst')
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
    command(cmd.format(cmd=_get_inkscape_cmd(),
                       dpi=dpi,
                       width=width,
                       target=target,
                       source=source))
    logger.info('generated image file {0}'.format(target))

def image_tasks(conf, app):
    paths = conf.paths

    meta_file = os.path.join(paths.projectroot, paths.images, 'metadata') + '.yaml'

    if not os.path.exists(meta_file):
        return

    images_meta = ingest_yaml_list(meta_file)

    if images_meta is None:
        return

    for image in images_meta:
        image['dir'] = paths.images
        source_base = os.path.join(paths.projectroot, image['dir'], image['name'])
        source_file = dot_concat(source_base, 'svg')
        rst_file = dot_concat(source_base, 'rst')
        image['conf'] = conf

        t = app.add('task')
        t.conf = conf
        t.job = generate_image_pages
        t.args = image
        t.description = "generating rst include file {0} for {1}".format(rst_file, source_file)
        t.target = rst_file
        t.dependency = meta_file
        logger.debug('adding task for image rst file: {0}'.format(rst_file))

        for output in image['output']:
            if 'tag' in output:
                tag = '-' + output['tag']
            else:
                tag = ''

            target_img = source_base + tag + '.png'

            inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 0.0 -e >/dev/null {target} {source}'

            t = app.add('task')
            t.conf = conf
            t.job = _generate_images
            t.args = [ inkscape_cmd, output['dpi'], output['width'], target_img, source_file ]
            t.target = target_img
            t.dependency = [ meta_file, source_file ]
            t.description = 'generating image file {0} from {1}'.format(target_img, source_file)
            logger.debug('adding image creation job for {0}'.format(target_img))
