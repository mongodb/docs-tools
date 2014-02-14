import sys
import os.path

from utils.strings import dot_concat
from utils.config import lazy_conf
from utils.shell import command
from utils.serialization import ingest_yaml_list
from utils.rstcloth.images import generate_image_pages

## Internal Supporting Methods

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
    print('[image]: generated image file {0}'.format(target))

def image_jobs(conf=None):
    conf = lazy_conf(None)
    paths = conf.paths

    meta_file = os.path.join(paths.images, 'metadata') + '.yaml'

    if not os.path.exists(meta_file):
        raise StopIteration

    images_meta = ingest_yaml_list(meta_file)

    if images_meta is None:
        raise StopIteration

    for image in images_meta:
        image['dir'] = paths.images
        source_base = os.path.join(image['dir'], image['name'])
        source_file = dot_concat(source_base, 'svg')
        rst_file = dot_concat(source_base, 'rst')
        image['conf'] = conf

        yield {
                'target': rst_file,
                'dependency': [ meta_file, os.path.join(paths.buildsystem, 'utils', 'rstcloth', 'images.py') ],
                'job': generate_image_pages,
                'args': image
              }

        for output in image['output']:
            if 'tag' in output:
                tag = '-' + output['tag']
            else:
                tag = ''

            target_img = source_base + tag + '.png'

            inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 0.0 -e >/dev/null {target} {source}'

            yield {
                    'target': target_img,
                    'dependency': [ source_file, meta_file ],
                    'job': _generate_images,
                    'args': [
                              inkscape_cmd,
                              output['dpi'],
                              output['width'],
                              target_img,
                              source_file
                            ],
                  }
