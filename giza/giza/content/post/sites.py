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
import subprocess
import shutil

logger = logging.getLogger('giza.content.post.sites')

from giza.tools.transformation import munge_page
from giza.tools.files import create_link, copy_if_needed
from giza.content.post.singlehtml import get_single_html_dir

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

        logger.info('error-pages: rendered {0} error pages'.format(idx))


def finalize_dirhtml_build(sconf, conf):
    builder = sconf.builder

    single_html_dir = get_single_html_dir(conf)
    search_page = os.path.join(conf.paths.branch_output, builder, 'index.html')

    if os.path.exists(search_page):
        copy_if_needed(source_file=search_page,
                       target_file=os.path.join(single_html_dir, 'search.html'))

    dest = os.path.join(conf.paths.projectroot, conf.paths.public_site_output)

    cmd_str = 'rsync -a {source}/ {destination}'.format(source=sconf.fq_build_output,
                                                        destination=dest)

    with open(os.devnull, 'w') as f:
        return_code = subprocess.call(args=cmd_str.split(),
                                      stdout=f,
                                      stderr=f)
        m = '"{0}" migrated build from {1} to {2}, with result {3}'
        logger.info(m.format(sconf.name, sconf.fq_build_output, dest, return_code))

    if 'excluded_files' in sconf:
        fns = [os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            fn)
               for fn in sconf['dirhtml']['excluded_files']]

        for fn in fns:
            if os.path.isdir(fn):
                shutil.rmtree(fn)
            elif os.path.isfile(fn):
                os.remove(fn)
            else:
                continue

            logger.info('removed file from dirhtml output directory: ' + fn)

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
        m = 'sitemap: configuration file {0} does not exist. Returning early'
        logger.error(m.format(config_path))
        return False

    sitemap = sitemap_gen.CreateSitemapFromFile(configpath=config_path,
                                                suppress_notify=True)
    if sitemap is None:
        logger.error('sitemap: failed to generate the sitemap due to encountered errors.')
        return False

    sitemap.Generate()

    logger.error('sitemap: generated sitemap according to the config file {0}'.format(config_path))
    return True
