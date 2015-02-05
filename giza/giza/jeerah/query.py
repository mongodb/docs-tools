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

from urllib import quote


def equality(user_input):
    return lazy_list(user_input, '=', 'in')


def inequality(user_input):
    return lazy_list(user_input, '!=', 'not in')


def escape_string(string):
    if ' ' in string or '.' in string:
        string = ''.join(['"', string, '"'])
    return string


def lazy_list(user_input, single, multi):
    if not isinstance(user_input, list):
        user_input = [escape_string(a) for a in user_input.split(',')]
    else:
        user_input = [escape_string(s) for s in user_input]

    if len(user_input) <= 1:
        return ' '.join([single, user_input[0]])
    else:
        return ' '.join([multi, '(', ", ".join(user_input), ')'])


def query_link(url, query_string):
    if url.endswith('/'):
        url = url[:-1]
    return '/'.join([url, 'issues', '?jql=' + quote(query_string)])


def strip_name(version):
    if version.startswith('"') and version.endswith('"'):
        version = version[1:-1]

    return version
