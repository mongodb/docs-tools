import re
import os
import logging

logger = logging.getLogger(os.path.basename(__file__))

from giza.tools.files import expand_tree

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

def manpage_url_tasks(builder, conf, app):
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
                                            builder), ['1', '5']):
        task = app.add('task')
        task.target = manpage
        task.job = manpage_url
        task.args = [regex_obj, manpage]
        task.description = 'processing urls in manpage file: {0}'.format(manpage)
