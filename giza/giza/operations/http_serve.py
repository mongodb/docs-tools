import sys
import os.path

if sys.version_info[0] == 2:
    import SocketServer as socket_server
    import SimpleHTTPServer as http_server
else:
    import socketserver as socket_server
    import http.server as http_server

import logging
logger = logging.getLogger('giza.operations.http')

import argh
from giza.config.helper import fetch_config


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
@argh.named('http')
def start(args):
    """Start an HTTP server rooted in the build directory."""
    config = fetch_config(args)


    if config.runstate.is_publish_target():
        root = config.paths.public_site_output
    else:
        root = os.path.join(config.paths.projectroot,
                            config.paths.branch_output,
                            args.builder[0])

    RequestHandler.root = root

    httpd = socket_server.TCPServer(('', config.runstate.port), RequestHandler)
    logger.info('Hosting {0} on port {1}'.format(root, config.runstate.port))
    httpd.serve_forever()
