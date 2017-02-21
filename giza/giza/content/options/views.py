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

logger = logging.getLogger('giza.content.options.views')


def render_options(option, conf):
    r = RstCloth()

    if 'program' not in option.replacement:
        option.replacement['program'] = RstCloth.role('program', option.program)

    if option.has_field('command'):
        option.replacement['command'] = RstCloth.role('toolcommand', option.command)

    if option.directive in ['option']:
        if len(option.name) > 1 and option.name[0] in ('<', '-'):
            prefix = ''
        else:
            prefix = '--'

        directive_str = '{prefix}{name}'

        if option.has_field('args'):
            directive_str += ' {args}'

        if option.has_field('aliases'):
            directive_str += ', {0}'.format(option.aliases)

            if option.has_field('args'):
                directive_str += ' {args}'

        if option.has_field('args'):
            directive_str = directive_str.format(prefix=prefix, name=option.name, args=option.args)
        else:
            directive_str = directive_str.format(prefix=prefix, name=option.name)
    else:
        prefix = ''
        directive_str = option.name

    if 'role' not in option.replacement:
        option.replacement['role'] = ':{0}:`{1}{2}`'.format(option.directive, prefix, option.name)

    option.render()  # jinja template render
    r.directive(option.directive, directive_str)
    r.newline()

    indent = 3
    if option.has_field('type'):
        r.content('*Type*: {0}'.format(option.type), indent=indent)
        r.newline()

    if option.has_field('default'):
        r.content('*Default*: {0}'.format(option.default), indent=indent)
        r.newline()

    for field in ('pre', 'description', 'content', 'post'):
        if option.has_field(field) is False:
            continue
        else:
            r.content(getattr(option, field).split('\n'), indent=indent, wrap=False)
            r.newline()

    return r
