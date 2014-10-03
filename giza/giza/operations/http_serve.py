import sys
import os.path
import logging
logger = logging.getLogger('giza.operations.http')

if sys.version_info[0] == 2:
    import SocketServer as socket_server
    import SimpleHTTPServer as http_server
else:
    import socketserver as socket_server
    import http.server as http_server

import argh
from giza.config.helper import fetch_config
from giza.tools.strings import hyph_concat

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
def start(args):
    """Start an HTTP server rooted in the build directory."""
    conf = fetch_config(args)

    if conf.runstate.is_publish_target():
        RequestHandler.root = conf.paths.public_site_output
    elif conf.runstate.edition is not None:
        RequestHandler.root = os.path.join(conf.paths.projectroot,
                                           conf.paths.branch_output,
                                           hyph_concat(args.builder[0], args.edition))
    else:
        RequestHandler.root = os.path.join(conf.paths.projectroot,
                                           conf.paths.branch_output,
                                           args.builder[0])

    httpd = socket_server.TCPServer(('', conf.runstate.port), RequestHandler)
    logger.info('Hosting {0} at http://localhost:{1}/'.format(RequestHandler.root, conf.runstate.port))
    httpd.serve_forever()
