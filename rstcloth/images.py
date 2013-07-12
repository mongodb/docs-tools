import sys
import os.path
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bin/')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import utils
from rstcloth import RstCloth

r = RstCloth()

def generate_image_pages(conf):
    image = '/'.join([conf['dir'], conf['name']])
    alt = conf['alt']
    b = conf['name']

    for output in conf['output']:
        if output['type'] == 'print':
            r.directive('only', 'latex', wrap=False, block=b)
        else:
            r.directive('only', 'not latex', wrap=False, block=b)

        r.newline()

        if 'tag' in output:
            tag = '-' + output['tag'] + '.png'
        else:
            tag = '.png'


        options = [('alt', alt), ('align', 'center'), ('figwidth', output['width'])]

        if 'scale' in output:
            options.append(('scale', output['scale']))

        r.directive(name='figure',
                    arg='/images/{0}{1}'.format(conf['name'], tag),
                    fields=options,
                    indent=3,
                    content=alt,
                    block=b)
        r.newline(block=b)

    r.write(image + '.rst')
    print('[image]: generated include file {0}.rst'.format(image))

def main():
    image = json.loads(sys.argv[1])
    generate_image_pages(image)

if __name__ == '__main__':
    main()
