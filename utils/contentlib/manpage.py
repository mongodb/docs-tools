import re
import os
import logging

logger = logging.getLogger(os.path.basename(__file__))

from utils.files import expand_tree
from utils.config import lazy_conf
from utils.transformations import process_page

#################### Manpage Processing ####################

def manpage_url(regex_obj, input_file):
    with open(input_file, 'r') as f:
        manpage = f.read()

    if isinstance(regex_obj, list):
        for regex, subst in regex_obj:
            manpage = regex.sub(subst, manpage)
    else:
        manpage = regex_obj[0].sub(regex_obj[1], manpage)

    with open(input_file, 'w') as f:
        f.write(manpage)

    logger.info("fixed urls in {0}".format(input_file))

def manpage_url_jobs(conf):
    project_source = os.path.join(conf.paths.projectroot,
                                  conf.paths.source)

    top_level_items = set()
    for fs_obj in os.listdir(project_source):
        if fs_obj.startswith('.static') or fs_obj == 'index.txt':
            continue
        if os.path.isdir(os.path.join(project_source, fs_obj)):
            top_level_items.add(fs_obj)
        if fs_obj.endswith('.txt'):
            top_level_items.add(fs_obj[:-4])

    top_level_items = '/'+ r'[^\s]*|/'.join(top_level_items) + r'[^\s]*'

    re_string = r'(\\fB({0})\\fP)'.format(top_level_items).replace(r'-', r'\-')
    subst = conf.project.url + '/' + conf.project.tag + r'\2'

    regex_obj = (re.compile(re_string), subst)

    for manpage in expand_tree(os.path.join(conf.paths.projectroot,
                                            conf.paths.output,
                                            conf.git.branches.current,
                                            'man'), ['1', '5']):
        yield dict(target=manpage,
                   dependency=None,
                   job=manpage_url,
                   args=[regex_obj, manpage])

def manpage_jobs(conf=None):
    conf = lazy_conf(conf)

    options_compat_re = [ (re.compile(r'\.\. option:: --'), r'.. setting:: ' ),
                          (re.compile(r'setting:: (\w+) .*'), r'setting:: \1'),
                          (re.compile(r':option:`--'), r':setting:`') ]


    jobs = [
        (
            os.path.join(conf.paths.includes, "manpage-options-auth.rst"),
            os.path.join(conf.paths.includes, 'manpage-options-auth-mongo.rst'),
            ( re.compile('fact-authentication-source-tool'),
              'fact-authentication-source-mongo' )
        ),
        (
            os.path.join(conf.paths.includes, 'manpage-options-ssl.rst'),
            os.path.join(conf.paths.includes, 'manpage-options-ssl-settings.rst'),
            options_compat_re
        ),
        (
            os.path.join(conf.paths.includes, 'manpage-options-audit.rst'),
            os.path.join(conf.paths.includes, 'manpage-options-audit-settings.rst'),
            options_compat_re
        )
    ]

    for input_fn, output_fn, regex in jobs:
        if os.path.exists(input_fn):
            yield {
                'target': output_fn,
                'dependency': input_fn,
                'job': process_page,
                'args': [ input_fn, output_fn, regex, 'manpage' ],
                'description': "generating manpage {0} from {1}".format(output_fn, input_fn)
              }
