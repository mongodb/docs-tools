import sys
import os.path
import re
import logging

logger = logging.getLogger(os.path.basename(__file__))

from giza.tools.shell import command
from giza.tools.serialization import ingest_yaml_list
from giza.tools.jobs.dependency import check_dependency
from giza.tools.files import (expand_tree, create_link, copy_if_needed,
                              decode_lines_from_file, encode_lines_to_file)
from giza.transformation import munge_page

def manual_single_html(input_file, output_file):
    # don't rebuild this if its not needed.
    if check_dependency(output_file, input_file) is False:
        logging.info('singlehtml not changed, not reprocessing.')
        return False
    else:
        text_lines = decode_lines_from_file(input_file)

        regexes = [
            (re.compile('href="contents.html'), 'href="index.html'),
            (re.compile('name="robots" content="index"'), 'name="robots" content="noindex"'),
            (re.compile('href="genindex.html'), 'href="../genindex/')
        ]

        for regex, subst in regexes:
            text_lines = [ regex.sub(subst, text) for text in text_lines ]

        encode_lines_to_file(output_file, text_lines)

        logging.info('processed singlehtml file.')

#################### Sphinx Post-Processing ####################

def finalize_epub_build(builder, conf):
    epub_name = '-'.join(conf.project.title.lower().split())
    epub_branched_filename = epub_name + '-' + conf.git.branches.current + '.epub'
    epub_src_filename = epub_name + '.epub'

    copy_if_needed(source_file=os.path.join(conf.paths.projectroot,
                                            conf.paths.branch_output,
                                            builder, epub_src_filename),
                   target_file=os.path.join(conf.paths.projectroot,
                                            conf.paths.public_site_output,
                                            epub_branched_filename))
    create_link(input_fn=epub_branched_filename,
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        epub_src_filename))


def get_single_html_dir(conf):
    return os.path.join(conf.paths.public_site_output, 'single')

def finalize_single_html_jobs(builder, conf):
    pjoin = os.path.join

    single_html_dir = get_single_html_dir(conf)

    if not os.path.exists(single_html_dir):
        os.makedirs(single_html_dir)

    try:
        manual_single_html(input_file=pjoin(conf.paths.branch_output,
                                                    builder, 'contents.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    except (IOError, OSError):
        manual_single_html(input_file=pjoin(conf.paths.branch_output,
                                                    builder, 'index.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    copy_if_needed(source_file=pjoin(conf.paths.branch_output,
                                     builder, 'objects.inv'),
                   target_file=pjoin(single_html_dir, 'objects.inv'))

    single_path = pjoin(single_html_dir, '_static')

    for fn in expand_tree(pjoin(conf.paths.branch_output,
                                builder, '_static'), None):

        yield {
            'job': copy_if_needed,
            'args': [fn, pjoin(single_path, os.path.basename(fn))],
            'target': None,
            'dependency': None
        }

def error_pages(builder, conf):
    error_conf = os.path.join(conf.paths.builddata, 'errors.yaml')

    if not os.path.exists(error_conf):
        return None
    else:
        error_pages = ingest_yaml_list(error_conf)

        sub = (re.compile(r'\.\./\.\./'), conf.project.url + r'/' + conf.project.tag + r'/')

        for error in error_pages:
            page = os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output, builder,
                                'meta', error, 'index.html')
            munge_page(fn=page, regex=sub, tag='error-pages')

        logging.info('error-pages: rendered {0} error pages'.format(len(error_pages)))

def finalize_dirhtml_build(builder, conf):
    pjoin = os.path.join

    single_html_dir = get_single_html_dir(conf)
    search_page = pjoin(conf.paths.branch_output, builder, 'index.html')

    if os.path.exists(search_page):
        copy_if_needed(source_file=search_page,
                       target_file=pjoin(single_html_dir, 'search.html'))

    dest = pjoin(conf.paths.projectroot, conf.paths.public_site_output)
    command('rsync -a {source}/ {destination}'.format(source=pjoin(conf.paths.projectroot,
                                                                 conf.paths.branch_output,
                                                                 builder),
                                                    destination=dest))

    logger.info('{0}: migrated build to {1}'.format(builder, dest))

    if conf.git.branches.current in conf.git.branches.published:
        sitemap_exists = sitemap(config_path=None, conf=conf)

        if sitemap_exists is True:
            copy_if_needed(source_file=pjoin(conf.paths.projectroot,
                                             conf.paths.branch_output,
                                             'sitemap.xml.gz'),
                           target_file=pjoin(conf.paths.projectroot,
                                             conf.paths.public_site_output,
                                             'sitemap.xml.gz'))

    sconf_path = pjoin(conf.paths.projectroot,
                       conf.paths.builddata, 'sphinx_yaml')
    sconf = ingest_yaml_doc()

    if 'dirhtml' in sconf and 'excluded_files' in sconf['dirhtml']:
        fns = [ pjoin(conf.paths.projectroot,
                      conf.paths.public_site_output,
                      fn)
                for fn in scont['dirhtml']['excluded_files'] ]

        cleaner(fns)
        logging.info('removed excluded files from dirhtml output directory')

def sitemap(config_path, conf):
    paths = conf.paths

    sys.path.append(os.path.join(paths.projectroot, paths.buildsystem, 'bin'))
    import sitemap_gen

    if config_path is None:
        config_path = os.path.join(paths.projectroot, 'conf-sitemap.xml')

    if not os.path.exists(config_path):
        logger.error('sitemap: configuration file {0} does not exist. Returning early'.format(config_path))
        return False

    sitemap = sitemap_gen.CreateSitemapFromFile(configpath=config_path,
                                                suppress_notify=True)
    if sitemap is None:
        logger.error('sitemap: failed to generate the sitemap due to encountered errors.')
        return False

    sitemap.Generate()

    logger.error('sitemap: generated sitemap according to the config file {0}'.format(config_path))
    return True
