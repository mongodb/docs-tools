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

import os.path

from giza.tools.strings import hyph_concat
from giza.tools.files import copy_if_needed, create_link, tarball

def html_tarball(builder, conf):
    copy_if_needed(os.path.join(conf.paths.projectroot,
                                conf.paths.includes, 'hash.rst'),
                   os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output,
                                builder, 'release.txt'))

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            hyph_concat(conf.project.name, ) + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    tarball(name=tarball_name,
            path=builder,
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.branch_output),
            newp=os.path.basename(basename))


    link_name = os.path.join(conf.paths.projectroot,
                             conf.paths.public_site_output,
                             conf.project.name + '.tar.gz')

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=link_name)

def slides_tarball(builder, conf):
    copy_if_needed(os.path.join(conf.paths.projectroot,
                                conf.paths.includes, 'hash.rst'),
                   os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output,
                                builder, 'release.txt'))

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            hyph_concat(conf.project.name,
                                        conf.git.branches.current,
                                        builder))

    tarball_fn = basename + '.tar.gz'

    tarball(name=tarball_fn,
            path=builder,
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.branch_output),
            newp=os.path.basename(basename))

    link_name = os.path.join(conf.paths.projectroot,
                             conf.paths.public_site_output,
                             hyph_concat(conf.project.name, 'slides') + '.tar.gz')

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_fn),
                 output_fn=link_name)

def man_tarball(builder, conf):
    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            'manpages-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'
    tarball(name=tarball_name,
            path=builder,
            cdir=os.path.join(conf.paths.projectroot, conf.paths.branch_output),
            newp=conf.project.name + '-manpages')


    link_name = os.path.join(conf.paths.projectroot,
                             conf.paths.public_site_output,
                             'manpages' + '.tar.gz')

    if os.path.exists(link_name):
        os.remove(link_name)

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=link_name)
