import sys
import os.path
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import utils
from rstcloth import RstCloth


def generate_image_pages(dir, name, alt, output):
    r = RstCloth()

    image = '/'.join([dir, name])
    alt = alt
    b = name

    for img_output in output:
        if img_output['type'] == 'print':
            r.directive('only', 'latex', wrap=False, block=b)
        else:
            r.directive('only', 'not latex', wrap=False, block=b)
            img_output['width'] = str(img_output['width']) + 'px'

        r.newline()

        if 'tag' in img_output:
            tag = '-' + img_output['tag'] + '.png'
        else:
            tag = '.png'


        options = [('alt', alt), ('align', 'center'), ('figwidth', img_output['width'])]

        if 'scale' in img_output:
            options.append(('scale', img_output['scale']))

        r.directive(name='figure',
                    arg='/images/{0}{1}'.format(name, tag),
                    fields=options,
                    indent=3,
                    content=alt,
                    block=b)
        r.newline(block=b)

    r.write(image + '.rst')
    print('[image]: generated include file {0}.rst'.format(image))

def main():
    image = json.loads(sys.argv[1])
    generate_image_pages(**image)

if __name__ == '__main__':
    main()
