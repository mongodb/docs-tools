import os.path
import sys

from fabric.api import task

from fabfile.make import runner

from fabfile.utils.serialization import ingest_yaml_list
from fabfile.utils.files import expand_tree
from fabfile.utils.config import lazy_conf

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'bin')))

from htaccess import generate_redirects, process_redirect

from fabfile.utils.contentlib.toc import toc_jobs
from fabfile.utils.contentlib.param import api_jobs
from fabfile.utils.contentlib.table import table_jobs
from fabfile.utils.contentlib.steps import steps_jobs
from fabfile.utils.contentlib.release import release_jobs
from fabfile.utils.contentlib.images import image_jobs
from fabfile.utils.contentlib.source import transfer_source
from fabfile.utils.contentlib.includes import write_include_index
from fabfile.utils.contentlib.robots import robots_txt_builder
from fabfile.utils.contentlib.options import option_jobs

### User facing fabric tasks

@task
def api():
    res = runner( api_jobs(), retval=True )

    print('[api]: generated {0} tables for api items'.format(len(res)))

@task
def tables():
    res = runner( table_jobs(), retval=True )

    print('[table]: built {0} tables'.format(len(res)))

#################### Generate Images and Related Content  ####################

## User facing fabric task

@task
def images():
    res = runner( image_jobs(), retval=True)

    print('[image]: rebuilt {0} rst and image files'.format(len(res)))

@task
def releases():
    res = runner( release_jobs(), retval=True )
    print('[releases]: completed regenerating {0} release files.'.format(len(res)))

#################### Copy of Source Directory for Build  ####################

@task
def source(conf=None):
    conf = lazy_conf(conf)

    transfer_source(conf)

#################### .htaccess files ####################

@task
def htaccess(fn='.htaccess'):
    conf = lazy_conf()

    in_files = ( i
                 for i in expand_tree(conf.paths.builddata, 'yaml')
                 if os.path.basename(i).startswith('htaccess') )

    sources = []
    for i in in_files:
        sources.extend(ingest_yaml_list(i))

    dirname = os.path.dirname(fn)
    if not dirname == '' and not os.path.exists(dirname):
        os.makedirs(dirname)

    lines = set( [ ] )

    for redir in sources:
        lines.add(generate_redirects(process_redirect(redir, conf), conf=conf, match=False))

    with open(fn, 'w') as f:
        f.writelines(lines)
        f.write('\n')
        f.writelines( ['<FilesMatch "\.(ttf|otf|eot|woff)$">','\n',
                       '   Header set Access-Control-Allow-Origin "*"', '\n'
                       '</FilesMatch>', '\n'] )

    print('[redirect]: regenerated {0} with {1} redirects ({2} lines)'.format(fn, len(sources), len(lines)))

@task
def robots(fn):
    conf = lazy_conf()

    robots_txt_builder(fn, conf, override=True)


#################### options ####################

@task
def options():
    conf = lazy_conf()

    res = runner( option_jobs(conf), retval=True )

    print('[options]: rendered {0} options'.format(len(res)))

@task
def steps():
    conf = lazy_conf()

    res = runner(steps_jobs(conf))

    print('[steps]: rendered {0} step files'.format(len(res)))

@task
def include_index():
    conf = lazy_conf()

    write_include_index(conf)
