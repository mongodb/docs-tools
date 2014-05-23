import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from docutils.core import publish_parts

from utils.config import lazy_conf
from utils.rstcloth.rstcloth import RstCloth

def generate_image_pages(dir, name, alt, output, conf=None):
    r = RstCloth()
    conf = lazy_conf(conf)

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
    logger.debug('generated include file {0}.rst'.format(image))
