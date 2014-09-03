#  2014 MongoDB, Inc.
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
import logging

logger = logging.getLogger('giza.content.post.sites')

from giza.tools.serialization import ingest_yaml_list

def make_redirect(conf):
    o = [ ]

    logger.info('generating {0} redirects'.format(len(conf.system.files.data.htaccess)))
    for redir in conf.system.files.data.htaccess:
        if redir.to.startswith('http'):
            url = redir.to
        else:
            url = conf.project.url + redir.to

        o.append(' '.join(['Redirect', str(redir.code), redir.from_loc, url, '\n']))

    o.sort()
    o.extend(['\n',
              '<FilesMatch "\.(ttf|otf|eot|woff)$">', '\n',
              '   Header set Access-Control-Allow-Origin "*"', '\n',
              '</FilesMatch>',
    ])

    return o

def write_redirects(conf):
    path = os.path.join(conf.paths.projectroot, conf.paths.htaccess)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, 'w') as f:
        f.writelines(make_redirect(conf))
        f.write('\n')

    logger.info('wrote redirects to: ' + path)

def redirect_tasks(conf, app):
    if 'htaccess' in conf.system.files.data:
        t = app.add('task')
        t.job = write_redirects
        t.args = [conf]
        t.description = 'generate and write redirects into: ' + conf.paths.htaccess
