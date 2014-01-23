import os.path
import sys
import argparse
import yaml
import utils

def process_redirect(redirect, conf=None):
    conf = utils.config.lazy_conf(conf)

    if 'all' in redirect['outputs']:
        redirect['outputs'].remove('all')
        for branch in conf.git.branches.published:
            redirect['outputs'].append(branch)

    for output in redirect['outputs']:
        if isinstance(output, dict):
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
        raise Exception(str(redirect['code']) + ' is not a supported redirect code')

    return redirect

def generate_match_rule(redir, base, conf=None):
    conf = utils.config.lazy_conf(conf)

    o = 'RedirectMatch {0} /({1}){2} {3}/$1{4}'

    return o.format(redir['code'], base, redir['redirect-path'],
                    conf.project.url, redir['url-base'])

def generate_simple_rule(redir, base=None, conf=None):
    conf = utils.config.lazy_conf(conf)

    if base is None:
        base = redir['outputs'][0]

    if isinstance(base, dict):
        left, right = base.items()[0]

        o = 'Redirect {0} /{1}{2} {3}/{4}{5}'

        return o.format(redir['code'], left, redir['redirect-path'],
                        conf.project.url, right, redir['url-base'])
    else:
        o = 'Redirect {0} /{1}{2} {3}/{1}{4}'

        return o.format(redir['code'], base, redir['redirect-path'],
                        conf.project.url, redir['url-base'])

def generate_external_rule(redir, base=None, conf=None):
    conf = utils.config.lazy_conf(conf)

    if base is None:
        base = redir['outputs'][0]

    o = 'Redirect {0} /{1}{2} {3}/{4}{5}'

    return o.format(redir['code'], base, redir['redirect-path'],
                    conf.project.url, redir['external'], redir['url-base'])

def determine_is_multi(targets):
    if len(targets) > 1:
        return True
    else:
        return False

def generate_redirects(redirect, match=False, conf=None):
    conf = utils.config.lazy_conf(conf)

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

    conf = utils.config.lazy_conf()


    lines = []
    for doc in utils.ingest_yaml(ui.data):
        if doc['type'] == 'redirect':
            lines.append(generate_redirects(process_redirect(doc, conf=conf), match=ui.match, conf=conf))
        if doc['type'] == 'redirect-draft':
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
