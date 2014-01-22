import os

from utils.serialization import ingest_yaml_list

def robots_txt_builder(fn, conf, override=False):
    if override is False:
        if conf.git.branches.current != 'master':
            print('[robots]: cowardly refusing to regenerate robots.txt on non-master branch.')
            return False
    else:
        print('[robots]: regenerating robots.txt on non-master branch with override.')

    suppressed = ingest_yaml_list(os.path.join(conf.paths.projectroot,
                                               conf.paths.builddata,
                                               'robots.yaml'))

    robots_txt_dir = os.path.dirname(fn)
    if not os.path.exists(robots_txt_dir):
        os.makedirs(robots_txt_dir)

    with open(fn, 'w') as f:
        f.write('User-agent: *')
        f.write('\n')
        for record in suppressed:
            page = record['file']
            if 'branches' not in record:
                f.write('Disallow: {0}'.format(page))
                f.write('\n')
            else:
                for branch in record['branches']:
                    if branch == '{{published}}':
                        for pbranch in conf.git.branches.published:
                            f.write('Disallow: /{0}{1}'.format(pbranch, page))
                            f.write('\n')
                    else:
                        f.write('Disallow: /{0}{1}'.format(branch,page))
                        f.write('\n')

    print('[robots]: regenerated robots.txt file.')
