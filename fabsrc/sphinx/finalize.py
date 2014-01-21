import os
import itertools

import fabfile.process as process
import fabfile.generate as generate
from fabfile.make import runner

from fabfile.utils.shell import command
from fabfile.utils.files import expand_tree, copy_if_needed, create_link
from fabfile.utils.config import BuildConfiguration, render_paths

def printer(string):
    print(string)

def finalize_build(builder, sconf, conf):
    if 'language' in sconf:
        # reinitialize conf and builders for internationalization
        conf.paths = render_paths(conf, sconf.language)
        builder = sconf.builder
        target = builder
    else:
        # mms compatibility
        target = builder
        builder = builder.split('-', 1)[0]

    jobs = {
        'linkcheck': [
            { 'job': printer,
              'args': ['[{0}]: See {1}/{0}/output.txt for output.'.format(builder, conf.paths.branch_output)]
            }
        ],
        'dirhtml': [
            { 'job': finalize_dirhtml_build,
              'args': [target, conf]
            }
        ],
        'json': process.json_output_jobs(conf),
        'singlehtml': finalize_single_html_jobs(target, conf),
        'latex': [
            { 'job': process.pdf_worker,
              'args': [target, conf]
            }
        ],
        'man': itertools.chain(process.manpage_url_jobs(conf), [
            { 'job': man_tarball,
              'args': [conf]
            }
        ]),
        'html': [
            { 'job': html_tarball,
              'args': [target, conf]
            }
        ],
        'gettext': process.gettext_jobs(conf),
        'all': [ ]
    }

    if builder not in jobs:
        jobs[builder] = []

    if conf.system.branched is True and conf.git.branches.current == 'master':
        jobs['all'].append(
            { 'job': generate.create_manual_symlink,
              'args': [conf]
            }
        )


    print('[sphinx] [post] [{0}]: running post-processing steps.'.format(builder))
    res = runner(itertools.chain(jobs[builder], jobs['all']), pool=1)
    print('[sphinx] [post] [{0}]: completed {1} post-processing steps'.format(builder, len(res)))


#################### Sphinx Post-Processing ####################

def finalize_epub_build(conf):
    epub_name = '-'.join(conf.project.title.lower().split())
    epub_branched_filename = epub_name + '-' + conf.git.branches.current + '.epub'
    epub_src_filename = epub_name + '.epub'

    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    copy_if_needed(source_file=os.path.join(conf.paths.projectroot,
                                            conf.paths.branch_output,
                                            'epub', epub_src_filename),
                   target_file=os.path.join(conf.paths.projectroot,
                                            conf.paths.public_site_output,
                                            epub_branched_filename))
    create_link(input_fn=epub_branched_filename,
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        epub_src_filename))


def get_single_html_dir(conf):
    return os.path.join(conf.paths.public_site_output, 'single')

def finalize_single_html_jobs(builder, conf):
    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        raise StopIteration

    pjoin = os.path.join

    single_html_dir = get_single_html_dir(conf)

    if not os.path.exists(single_html_dir):
        os.makedirs(single_html_dir)

    try:
        process.manual_single_html(input_file=pjoin(conf.paths.branch_output,
                                                    builder, 'contents.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    except (IOError, OSError):
        process.manual_single_html(input_file=pjoin(conf.paths.branch_output,
                                                    builder, 'index.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    copy_if_needed(source_file=pjoin(conf.paths.branch_output,
                                     builder, 'objects.inv'),
                   target_file=pjoin(single_html_dir, 'objects.inv'))

    single_path = pjoin(single_html_dir, '_static')

    for fn in expand_tree(pjoin(conf.paths.branch_output,
                                builder, '_static'), None):

        yield {
            'job': copy_if_needed,
            'args': [fn, pjoin(single_path, os.path.basename(fn))],
            'target': None,
            'dependency': None
        }

def finalize_dirhtml_build(builder, conf):
    pjoin = os.path.join

    process.error_pages(conf)

    single_html_dir = get_single_html_dir(conf)
    search_page = pjoin(conf.paths.branch_output, builder, 'index.html')

    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    if os.path.exists(search_page):
        copy_if_needed(source_file=search_page,
                       target_file=pjoin(single_html_dir, 'search.html'))

    dest = pjoin(conf.paths.projectroot, conf.paths.public_site_output)
    command('rsync -a {source}/ {destination}'.format(source=pjoin(conf.paths.projectroot,
                                                                 conf.paths.branch_output,
                                                                 builder),
                                                    destination=dest))

    print('[{0}]: migrated build to {1}'.format(builder, dest))

    if conf.git.branches.current in conf.git.branches.published:
        sitemap_exists = generate.sitemap(config_path=None, conf=conf)

        if sitemap_exists is True:
            copy_if_needed(source_file=pjoin(conf.paths.projectroot,
                                             conf.paths.branch_output,
                                             'sitemap.xml.gz'),
                           target_file=pjoin(conf.paths.projectroot,
                                             conf.paths.public_site_output,
                                             'sitemap.xml.gz'))

    sconf = BuildConfiguration('sphinx.yaml', pjoin(conf.paths.projectroot,
                                                conf.paths.builddata))

    if 'dirhtml' in sconf and 'excluded_files' in sconf.dirhtml:
        fns = [ pjoin(conf.paths.projectroot,
                      conf.paths.public_site_output,
                      fn)
                for fn in sconf.dirhtml.excluded_files ]

        cleaner(fns)
        print('[dirhtml] [clean]: removed excluded files from output directory')


#################### Associated Sphinx Artifacts ####################

def html_tarball(builder, conf):
    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    copy_if_needed(os.path.join(conf.paths.projectroot,
                                conf.paths.includes, 'hash.rst'),
                   os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output,
                                'html', 'release.txt'))

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    generate.tarball(name=tarball_name,
                     path='html',
                     cdir=os.path.join(conf.paths.projectroot,
                                       conf.paths.branch_output),
                     sourcep='html',
                     newp=os.path.basename(basename))

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        conf.project.name + '.tar.gz'))

def man_tarball(conf):
    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.branch_output,
                            'manpages-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'
    generate.tarball(name=tarball_name,
                     path='man',
                     cdir=os.path.dirname(basename),
                     sourcep='man',
                     newp=conf.project.name + '-manpages'
                     )

    copy_if_needed(tarball_name,
                   os.path.join(conf.paths.projectroot,
                                conf.paths.public_site_output,
                                os.path.basename(tarball_name)))

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        'manpages' + '.tar.gz'))
