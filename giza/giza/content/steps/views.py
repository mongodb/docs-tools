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

from giza.content.helper import character_levels
from rstcloth.rstcloth import RstCloth

logger = logging.getLogger('giza.content.steps.views')


def render_steps(steps, conf):
    r = RstCloth()

    header_html = ('<div class="sequence-block">'
                   '<div class="bullet-block">'
                   '<div class="sequence-step">'
                   '{0}'
                   '</div>'
                   '</div>')

    for idx, step in enumerate(steps.ordered_content()):
        step.render()  # run replacements

        if 'number' not in step:
            step.number = idx

        r.directive('only', 'html or dirhtml or singlehtml')
        r.newline()

        r.directive(name='raw',
                    arg='html',
                    content=header_html.format(step.number),
                    indent=3)
        r.newline()

        if 'heading' in step:
            r.heading(text=step.heading,
                      char=character_levels[step.level],
                      indent=3)
            r.newline()

        render_step_content(step, 3, r)

        r.directive(name='raw',
                    arg='html',
                    content="</div>",
                    indent=3)
        r.newline()

        r.directive('only', 'not(html or dirhtml or singlehtml)')
        r.newline()

        if 'heading' in step:
            r.heading(text="Step {0}: {1}".format(step.number, step.heading),
                      char=character_levels[step.level],
                      indent=3)
            r.newline()
        else:
            r.heading(text="Step {0}".format(step.number),
                      char=character_levels[step.level],
                      indent=3)
            r.newline()

        render_step_content(step, 3, r)

    return r


def render_step_content(step, indent, r):
    if 'pre' in step:
        r.content(content=step.pre,
                  indent=indent,
                  wrap=False)
        r.newline()

    if 'action' in step:
        for action in step.action:
            action.replacement = step.replacement
            action.render()
            render_action(action, indent, step.level + 1, r)

    if 'content' in step:
        r.content(content=step.content,
                  indent=indent,
                  wrap=False)
        r.newline()

    if 'post' in step:
        r.content(content=step.post,
                  indent=indent,
                  wrap=False)
        r.newline()


def render_action(action, indent, level, r):
    if 'heading' in action:
        if level in ('title', 0, 1):
            r.titleg(text=action.heading,
                     char=character_levels[level],
                     indent=indent)
        else:
            r.heading(text=action.heading,
                      char=character_levels[level],
                      indent=indent)
        r.newline()

    if 'pre' in action:
        r.content(content=action.pre,
                  indent=indent,
                  wrap=False)
        r.newline()

    if 'code' in action:
        if action.copyable:
            r.directive(name='cssclass', arg='copyable-code', indent=indent)
            r.newline()

        r.directive(name='code-block',
                    arg=action.language,
                    indent=indent,
                    content=action.code,
                    wrap=False)
        r.newline()

    if 'content' in action:
        r.content(content=action.content,
                  indent=indent,
                  wrap=False)
        r.newline()

    if 'post' in action:
        r.content(content=action.post,
                  indent=indent,
                  wrap=False)
        r.newline()
