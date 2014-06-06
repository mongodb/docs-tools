import json
import re
import os
import logging

logger = logging.getLogger(os.path.basename(__file__))

from utils.config import lazy_conf
from utils.shell import command
from utils.strings import dot_concat
from utils.files import expand_tree, copy_if_needed
from utils.transformations import munge_content

########## Process Sphinx Json Output ##########

def json_output(conf):
    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')
    public_list_file = os.path.join(conf.paths.public_site_output,
                                    'json', '.file_list')

    cmd = 'rsync --recursive --times --delete --exclude="*pickle" --exclude=".buildinfo" --exclude="*fjson" {src} {dst}'

    json_dst = os.path.join(conf.paths.public_site_output, 'json')

    if not os.path.exists(json_dst):
        logger.debug('created directories for {0}'.format(json_dst))
        os.makedirs(json_dst)

    builder = 'json'
    if 'edition' in conf.project:
        builder += '-' + conf.project.edition

    command(cmd.format(src=os.path.join(conf.paths.branch_output, builder) + '/',
                       dst=json_dst))

    copy_if_needed(list_file, public_list_file)
    logger.info('deployed json files to local staging.')

def json_output_jobs(conf):

    regexes = [
        (re.compile(r'<a class=\"headerlink\"'), '<a'),
        (re.compile(r'<[^>]*>'), ''),
        (re.compile(r'&#8220;'), '"'),
        (re.compile(r'&#8221;'), '"'),
        (re.compile(r'&#8216;'), "'"),
        (re.compile(r'&#8217;'), "'"),
        (re.compile(r'&#\d{4};'), ''),
        (re.compile(r'&nbsp;'), ''),
        (re.compile(r'&gt;'), '>'),
        (re.compile(r'&lt;'), '<')
    ]

    outputs = []
    for fn in expand_tree('source', 'txt'):
        # path = build/<branch>/json/<filename>

        path = os.path.join(conf.paths.branch_output,
                            'json', os.path.splitext(fn.split(os.path.sep, 1)[1])[0])
        fjson = dot_concat(path, 'fjson')
        json = dot_concat(path, 'json')

        if conf.project.name == 'mms':
            if not os.path.exists(fjson):
                continue

        yield { 'target': json,
                'dependency': fjson,
                'job': process_json_file,
                'description': "processing json file".format(json),
                'args': (fjson, json, regexes, conf) }

        outputs.append(json)

    list_file = os.path.join(conf.paths.branch_output, 'json-file-list')

    yield { 'target': list_file,
            'dependency': None,
            'description': 'generating json index list {0}'.format(list_file),
            'job': generate_list_file,
            'args': (outputs, list_file, conf) }

    json_output(conf)

def process_json_file(input_fn, output_fn, regexes, conf=None):
    with open(input_fn, 'r') as f:
        document = f.read()

    doc = json.loads(document)

    if 'body' in doc:
        text = doc['body'].encode('ascii', 'ignore')
        text = munge_content(text, regexes)

        doc['text'] = ' '.join(text.split('\n')).strip()

    if 'title' in doc:
        title = doc['title'].encode('ascii', 'ignore')
        title = munge_content(title, regexes)

        doc['title'] = title

    url = [ conf.project.url, conf.project.basepath ]
    url.extend(input_fn.rsplit('.', 1)[0].split(os.path.sep)[3:])

    doc['url'] = '/'.join(url) + '/'

    with open(output_fn, 'w') as f:
        f.write(json.dumps(doc))

def generate_list_file(outputs, path, conf):
    dirname = os.path.dirname(path)

    url = '/'.join([ conf.project.url, conf.project.basepath, 'json' ])

    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(path, 'w') as f:
        for fn in outputs:
            f.write( '/'.join([ url, fn.split('/', 3)[3:][0]]) )
            f.write('\n')

    logger.info('rebuilt inventory of json output.')
