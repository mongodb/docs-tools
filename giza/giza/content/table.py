import os.path
import logging

logger = logging.getLogger(os.path.basename(__file__))

from rstcloth.table import TableBuilder, YamlTable, ListTable

from giza.tools.strings import dot_concat, hyph_concat
from giza.tools.files import expand_tree

#################### Table Builder ####################

def _get_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return dot_concat(os.path.join(base, 'table', leaf[6:]), 'rst')

def _get_list_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return dot_concat(hyph_concat(os.path.join(base, 'table', leaf[6:]), 'list'), 'rst')

def make_parent_dirs(*paths):
    for path in paths:
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

def _generate_tables(source, target, list_target):
    table_data = YamlTable(source)

    make_parent_dirs(target, list_target)

    # if not table_data.format or table_data.format is None:
    #     build_all = True

    list_table = TableBuilder(ListTable(table_data))
    list_table.write(list_target)
    logger.debug('rebuilt rendered table {0}'.format(list_target))

    list_table.write(target)
    logger.debug('rebuilt rendered list table {0}'.format(target))

    # if build_all or table_data.format == 'list':
    #     list_table = TableBuilder(ListTable(table_data))
    #     list_table.write(list_target)
    #     print('[table]: rebuilt {0}'.format(list_target))
    # if build_all or table_data.format == 'rst':
    #     # this really ought to be RstTable, but there's a bug there.
    #     rst_table = TableBuilder(ListTable(table_data))
    #     rst_table.write(target)

    #     print('[table]: rebuilt {0} as (a list table)'.format(target))

    logger.info('rebuilt rendered table output for {0}'.format(source))

def table_tasks(conf, app):
    for source in expand_tree(os.path.join(conf.paths.projectroot, conf.paths.includes), 'yaml'):
        if os.path.basename(source).startswith('table'):
            target = _get_table_output_name(source)
            list_target = _get_list_table_output_name(source)

            t = app.add('task')
            t.target = [ target, list_target ]
            t.dependency = source
            t.job = _generate_tables
            t.args = [ source, target, list_target ]
            t.description = 'generating tables: {0}, {1} from'.format(target, list_target, source)

            logger.info('adding table job to build: {0}'.format(target))
