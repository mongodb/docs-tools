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

import logging

from rstcloth.rstcloth import RstCloth

from giza.content.steps.views import render_action

logger = logging.getLogger('giza.content.release.views')


def render_releases(release, conf):
    r = RstCloth()

    release.replacement = {
        'version': conf.version.release,
        'branch': conf.version.branch,
        'stable': conf.version.stable,
    }

    release.render()  # run replacements

    render_action(release, indent=0, level=2, r=r)

    return r
