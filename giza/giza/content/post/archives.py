# Copyright 2014 MongoDB, Inc.
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

"""
Worker functions that create artifacts for archives of build targets that are
distributed as tarballs (i.e. html sites, manpages, and slides) for offline use.
"""

import os
import logging

from giza.tools.files import create_link, tarball

logger = logging.getLogger('giza.content.post.archives')


def get_tarball_name(builder, conf):
    if builder == 'link-html':
        fn = conf.project.name + '.tar.gz'
    elif builder == 'link-man':
        fn = "manpages.tar.gz"
    elif builder == 'link-slides':
        fn = ''.join((conf.project.name, '-', 'slides', '.tar.gz'))
    elif builder.startswith('man'):
        fn = ''.join(('manpages', '-', conf.git.branches.current, '.tar.gz'))
    elif builder.startswith('html'):
        fn = ''.join((conf.project.name, '-', conf.git.branches.current, '.tar.gz'))
    else:
        fn = ''.join((conf.project.name, '-', conf.git.branches.current, builder, '.tar.gz'))

    if conf.project.edition != conf.project.name:
        fn = fn.replace(conf.project.name, '-'.join((conf.project.name, conf.project.edition)))

    return os.path.join(conf.paths.projectroot,
                        conf.paths.public_site_output,
                        fn)


def html_tarball(builder, artifact_loc, conf):
    tarball_name = get_tarball_name('html', conf)

    tarball(name=tarball_name,
            path=artifact_loc,
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.branch_output),
            newp=os.path.splitext(os.path.basename(tarball_name))[0])

    link_name = get_tarball_name('link-html', conf)

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_name),
                output_fn=link_name)


def slides_tarball(builder, artifact_loc, conf):
    tarball_name = get_tarball_name('slides', conf)

    tarball(name=tarball_name,
            path=artifact_loc,
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.branch_output),
            newp=os.path.splitext(os.path.basename(tarball_name))[0])

    link_name = get_tarball_name('link-slides', conf)

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_name),
                output_fn=link_name)


def man_tarball(builder, artifact_loc, conf):
    tarball_name = get_tarball_name('man', conf)

    tarball(name=tarball_name,
            path=artifact_loc,
            cdir=os.path.join(conf.paths.projectroot, conf.paths.branch_output),
            newp=conf.project.name + '-manpages')

    link_name = get_tarball_name('link-man', conf)

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_name),
                output_fn=link_name)
