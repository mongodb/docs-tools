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

logger = logging.getLogger('giza.content.steps.views')

from giza.content.helper import edition_check, character_levels
from rstcloth.rstcloth import RstCloth

def render_steps(steps, conf):
    r = RstCloth()

    header_html = ('<div class="sequence-block">' '<div class="bullet-block">'
                   '<div class="sequence-step">' '{0}' '</div>' '</div>')

    for idx, step in enumerate(steps.steps):
        if edition_check(step, conf) is False:
            continue
        if 'number' not in step:
            step.number = idx

        r.directive('only', 'web')
        r.newline()

        r.directive(name='raw',
                    arg='html',
                    content=header_html.format(step.number),
                    indent=3)
        r.newline()

        r.heading(text=step.heading,
                  char=character_levels[step.level],
                  indent=3)
        r.newline()

        if ('pre' in step or 'action' in step or 'content' in step or 'post' in step):
            r.directive(name='class',
                        arg='step-' + str(step.number),
                        indent=3)
            r.newline()

        render_step_content(step, 6, r)

        r.directive('only', 'print')
        r.newline()

        r.heading(text="Step {0}: {1}".format(step.number, step.heading),
                  char=character_levels[step.level],
                  indent=3)
        r.newline()

        render_step_content(step, 3, r)

    return r

def render_step_content(step, indent, r):
    if 'pre' in step:
        r.content(content=step.pre,
                  indent=indent)
        r.newline()

    if 'action' in step:
        for action in step.action:
            render_action(action, indent, r)

    if 'content' in step:
        r.content(content=step.content,
                  indent=indent)
        r.newline()

    if 'post' in step:
        r.content(content=step.post,
                  indent=indent)
        r.newline()

def render_action(action, indent, r):
    if 'heading' in action:
        r.heading(text=action.heading,
                  char=character_levels[action.level],
                  indent=indent)
        r.newline()

    if 'pre' in action:
        r.content(content=action.pre,
                  indent=indent)
        r.newline()

    if 'code' in action:
        r.directive(name='code-block',
                    arg=action.language,
                    indent=indent,
                    content=action.code)
        r.newline()

    if 'content' in action:
        r.content(content=action.content,
                  indent=indent)
        r.newline()

    if 'post' in action:
        r.content(content=action.post,
                  indent=indent)
        r.newline()
