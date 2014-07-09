import os
import logging

logger = logging.getLogger('giza.content.robots')

from giza.serialization import ingest_yaml_list

def robots_txt_builder(fn, conf, override=False):
    if override is False:
        if conf.git.branches.current != 'master':
            logger.info('cowardly refusing to regenerate robots.txt on non-master branch.')
            return False
    else:
        logger.info('regenerating robots.txt on non-master branch with override.')

    if 'robots' not in conf.system.files.data:
        logger.warning('no robots directives configured. not generating robots.txt')
        return

    robots_txt_dir = os.path.dirname(fn)
    if not os.path.exists(robots_txt_dir):
        os.makedirs(robots_txt_dir)

    with open(fn, 'w') as f:
        f.write('User-agent: *')
        f.write('\n')
        for record in conf.system.files.data.robots:
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

    logger.info('regenerated robots.txt file.')

def robots_txt_tasks(conf, app):
    if 'robots' in conf.system.files.data and len(conf.system.files.data.robots) > 0:
        t = app.add('task')
        t.job = robots_txt_builder
        t.args = [ os.path.join(conf.paths.projectroot,
                                conf.paths.public,
                                'robots.txt'), conf ]
