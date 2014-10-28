# 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os.path
import re
import sys

logger = logging.getLogger('giza.content.post.sites')

from giza.core.task import check_dependency
from giza.tools.command import command
from giza.tools.serialization import ingest_yaml_list, ingest_yaml_doc
from giza.tools.transformation import munge_page
from giza.tools.files import (expand_tree, create_link, copy_if_needed,
                              decode_lines_from_file, encode_lines_to_file,
                              safe_create_directory)

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


def error_pages(sconf, conf):
    builder = sconf.builder

    if 'errors' not in conf.system.files.data:
        return None
    else:
        sub = (re.compile(r'\.\./\.\./'), conf.project.url + r'/' + conf.project.tag + r'/')

        for idx, error in enumerate(conf.system.files.data.errors):
            page = os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output, builder,
                                'meta', error, 'index.html')
            munge_page(fn=page, regex=sub, tag='error-pages')

        logging.info('error-pages: rendered {0} error pages'.format(idx))

def finalize_dirhtml_build(sconf, conf):
    builder = sconf.builder

    single_html_dir = get_single_html_dir(conf)
    search_page = os.path.join(conf.paths.branch_output, builder, 'index.html')

    if os.path.exists(search_page):
        copy_if_needed(source_file=search_page,
                       target_file=os.path.join(single_html_dir, 'search.html'))

    dest = os.path.join(conf.paths.projectroot, conf.paths.public_site_output)
    m_cmd = command('rsync -a {source}/ {destination}'.format(source=sconf.build_output,
                                                              destination=dest))

    logger.info('"{0}" migrated build from {1} to {2}, with result {3}'.format(sconf.name, sconf.build_output, dest, m_cmd.return_code))

    if 'excluded_files' in sconf:
        fns = [ os.path.join(conf.paths.projectroot,
                      conf.paths.public_site_output,
                      fn)
                for fn in sconf['dirhtml']['excluded_files'] ]

        cleaner(fns)
        logging.info('removed excluded files from dirhtml output directory')

    if conf.git.branches.current in conf.git.branches.published:
        sitemap_exists = sitemap(config_path=None, conf=conf)

        legacy_sitemap_fn = os.path.join(conf.paths.projectroot,
                                         conf.paths.branch_output,
                                         'sitemap.xml.gz')

        if os.path.exists(legacy_sitemap_fn) and sitemap_exists is True:
            copy_if_needed(source_file=legacy_sitemap_fn,
                           target_file=os.path.join(conf.paths.projectroot,
                                                    conf.paths.public_site_output,
                                                    'sitemap.xml.gz'))


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
