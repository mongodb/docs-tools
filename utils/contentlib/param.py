import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from utils.config import lazy_conf
from utils.strings import dot_concat
from utils.files import expand_tree
from utils.serialization import ingest_yaml_list
from utils.rstcloth.param import generate_params

def api_jobs(conf=None):
    conf = lazy_conf(conf)

    for source in expand_tree(os.path.join(conf.paths.projectroot, conf.paths.source, 'reference'), 'yaml'):
        target = dot_concat(os.path.splitext(source)[0], 'rst')

        yield {
                'target': target,
                'dependency': source,
                'job': _generate_api_param,
                'args': [source, target, conf]
              }


def _generate_api_param(source, target, conf):
    r = generate_params(ingest_yaml_list(source), source, conf)
    r.write(target)

    logger.info('rebuilt {0}'.format(target))
