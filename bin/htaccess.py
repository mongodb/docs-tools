import argparse
import logging
import os.path
import sys

logger = logging.getLogger(os.path.basename(__file__))

import yaml

from utils.serialization import ingest_yaml
from utils.config import lazy_conf
from utils.strings import slash_concat

def redirect_schema_migration(redir):
    """
    Translate redirection documents to use more sensible field names.
    """

    o = {}

    if 'url-base' in redir:
        o['to'] = redir['url-base']
        del redir['url-base']
    if 'redirect-path' in redir:
        o['from'] = redir['redirect-path']
        del redir['redirect-path']

    o.update(redir)

    return o

def process_redirect(redirect, conf=None):
    """Given a redirection document, returns a properly formatted string for an
    Apache htaccess redirect statement."""

    conf = lazy_conf(conf)

    redirect = redirect_schema_migration(redirect)

    if 'all' in redirect['outputs']:
        redirect['outputs'].remove('all')
        redirect['outputs'].extend(conf.git.branches.published)

    for output in redirect['outputs']:
        if isinstance(output, dict):
            source, target = output.items()[0]

            if isinstance(target, dict):
                left, right = target.items()[0]

                if source.startswith('after-'):
                    redirect['outputs'].remove(output)
                    idx = conf.git.branches.published.index(source.split('-', 1)[1])

                    for out in conf.git.branches.published[:idx]:
                        redirect['outputs'].append({ slash_concat(left, out): slash_concat(right,out) })
                elif source.startswith('before-'):
                    redirect['outputs'].remove(output)
                    idx = conf.git.branches.published.index(source.split('-', 1)[1])

                    for out in conf.git.branches.published[idx:]:
                        redirect['outputs'].append({ slash_concat(left, out): slash_concat(right,out) })
                else:
                    logger.error("{0} is invalid source for redirect: {1}".format(source, redirect))
            else:
                continue
        elif output.startswith('after-'):
            idx = conf.git.branches.published.index(output.split('-', 1)[1])

            redirect['outputs'].remove(output)
            redirect['outputs'].extend(conf.git.branches.published[:idx])
        elif output.startswith('before-'):
            idx = conf.git.branches.published.index(output.split('-', 1)[1])

            redirect['outputs'].remove(output)
            redirect['outputs'].extend(conf.git.branches.published[idx:])

    if redirect['code'] in [ 301, 302, 303 ]:
        redirect['code'] = str(redirect['code'])
    else:
        msg = str(redirect['code']) + ' is not a supported redirect code'
        logger.critical(msg)
        raise Exception(msg)

    return redirect

def generate_match_rule(redir, base, conf=None):
    conf = lazy_conf(conf)

    o = 'RedirectMatch {0} /({1}){2} {3}/$1{4}'

    return o.format(redir['code'], base, redir['from'],
                    conf.project.url, redir['to'])

def generate_simple_rule(redir, base=None, conf=None):
    conf = lazy_conf(conf)

    if base is None:
        base = redir['outputs'][0]

    if isinstance(base, dict):
        left, right = base.items()[0]

        o = 'Redirect {0} /{1}{2} {3}/{4}{5}'

        return o.format(redir['code'], left, redir['from'],
                        conf.project.url, right, redir['to'])
    else:
        o = 'Redirect {0} /{1}{2} {3}/{1}{4}'

        return o.format(redir['code'], base, redir['from'],
                        conf.project.url, redir['to'])

def generate_external_rule(redir, base=None, conf=None):
    conf = lazy_conf(conf)

    if base is None:
        base = redir['outputs'][0]

    if redir['external'].startswith('http'):
        o = 'Redirect {0} /{1}{2} {3}/{4}'
        return o.format(redir['code'], base, redir['from'],
                        redir['external'], redir['to'])
    else:
        o = 'Redirect {0} /{1}{2} {3}/{4}{5}'

        return o.format(redir['code'], base, redir['from'],
                        conf.project.url, redir['external'], redir['to'])

def determine_is_multi(targets):
    if len(targets) > 1:
        return True
    else:
        return False

def generate_redirects(redirect, match=False, conf=None):
    conf = lazy_conf(conf)

    multi = determine_is_multi(redirect['outputs'])

    if 'external' in redirect:
        o = ''
        for output in redirect['outputs']:
            o += generate_external_rule(redirect, output, conf)
            o += '\n'
    elif multi and match is True:
        _base = ''
        for path in redirect['outputs']:
            _base += path + '|'
        base = _base[:-1]

        o = generate_match_rule(redirect, base, conf)
        o += '\n'
    elif multi is True and match is False:
        o = ''
        for output in redirect['outputs']:
            o += generate_simple_rule(redirect, output, conf)
            o += '\n'
    elif multi is False:
        o = generate_simple_rule(redirect, conf=conf)
        o += '\n'

    return o

def user_input():
    parser = argparse.ArgumentParser('.htaccess generator.')
    parser.add_argument('filename', nargs='?', default='.htaccess',
                        help='the name of the file to generate. Defaults to ".htaccess"')
    parser.add_argument('--match', '-m', action='store_true', default=False,
                        help='generate RedirectMatch if specified, rather than the default Redirect rules.')
    parser.add_argument('--data', '-d', action='store',
                        help='the .yaml file containing the redirect information.')
    return parser.parse_args()

def main():
    ui = user_input()

    conf = lazy_conf()

    lines = []
    for doc in ingest_yaml(ui.data):
        if doc['type'] == 'redirect':
            lines.append(generate_redirects(process_redirect(doc, conf=conf), match=ui.match, conf=conf))
        if doc['type'] == 'draft':
            print(generate_redirects(process_redirect(doc, conf=conf), match=ui.match, conf=conf))

    if lines:
        dirname = os.path.dirname(ui.filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(ui.filename, 'w') as f:
            for line in lines:
                f.write(line)

        print('[redirect]: regenerated ' + ui.filename + ' file.' )

if __name__ == '__main__':
    main()
