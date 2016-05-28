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
Development server in giza for more realistic local previews of rendered pages.
"""

import sys
import os.path
import logging
import argh

from giza.config.helper import fetch_config

logger = logging.getLogger('giza.operations.http')

if sys.version_info[0] == 2:
    import SocketServer as socket_server
    import SimpleHTTPServer as http_server
else:
    import socketserver as socket_server
    import http.server as http_server


class RequestHandler(http_server.SimpleHTTPRequestHandler):

    """Request handler wrapper that hosts files rooted at a particular
       directory."""

    def translate_path(self, path):
        """Map a request into the build/ directory."""
        path = os.path.relpath(path, '/')
        return os.path.join(self.root, path)

    def log_message(self, fmt, *args):
        """Pass this server event into the operation logger."""
        logger.info(fmt % args)


@argh.arg('--port', '-p', default=8090, dest='port')
@argh.arg('--builder', '-b', nargs='*', default='publish')
@argh.arg('--edition', '-e')
@argh.named('http')
@argh.expects_obj
def start(args):
    """Start an HTTP server rooted in the build directory."""
    conf = fetch_config(args)

    if conf.runstate.is_publish_target():
        RequestHandler.root = conf.paths.public_site_output
    elif conf.runstate.edition is not None:
        RequestHandler.root = os.path.join(conf.paths.projectroot,
                                           conf.paths.branch_output,
                                           '-'.join((args.builder[0], args.edition)))
    else:
        RequestHandler.root = os.path.join(conf.paths.projectroot,
                                           conf.paths.branch_output,
                                           args.builder[0])

    httpd = socket_server.TCPServer(('', conf.runstate.port), RequestHandler)
    logger.info('Hosting {0} at http://localhost:{1}/'.format(RequestHandler.root,
                                                              conf.runstate.port))
    httpd.serve_forever()
