import datetime
import itertools
import os
import re
import pkg_resources
import sys

from multiprocessing import cpu_count

from fabric.api import local, task, hide, settings, quiet
from fabric.utils import puts

import generate
import process
import mms

from clean import cleaner
from make import runner
from intersphinx import intersphinx, intersphinx_jobs

from utils.config import lazy_conf, BuildConfiguration, render_paths
from utils.files import expand_tree, copy_if_needed, create_link
from utils.output import swap_streams, build_platform_notification
from utils.serialization import ingest_json
from utils.strings import hyph_concat
from utils.structures import AttributeDict
from utils.project import edition_setup
from utils.jobs.dependency import dump_file_hashes
from utils.jobs.errors import PoolResultsError

intersphinx = task(intersphinx)

@task
def target(*targets):
    conf = lazy_conf()

    build_prerequisites(conf)

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    if len(targets) == 0:
        targets.append('html')

    target_jobs = []

    for target in targets:
        if target in sconf:
            target_jobs.append({
                'job': build_worker_wrapper,
                'args': [ target, sconf, conf]
            })
        else:
            print('[sphinx] [warning]: not building {0} without configuration.'.format(target))

    if len(target_jobs) <= 1:
        res = runner(target_jobs, pool=1)
    else:
        res = runner(target_jobs, pool=3, parallel='process')

    print('[sphinx]: build {0} sphinx targets'.format(len(res)))

def get_tags(target, sconf):
    ret = set()

    ret.add(target)
    ret.add(target.split('-')[0])

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.add('website')
    else:
        ret.add('print')

    if 'edition' in sconf:
        ret.add(sconf.edition)

    return ' '.join([' '.join(['-t', i ])
                     for i in ret
                     if i is not None])

def timestamp(form='filename'):
    if form == 'filename':
        return datetime.datetime.now().strftime("%Y-%m-%d.%H-%M")
    else:
        return datetime.datetime.now().strftime("%Y-%m-%d, %H:%M %p")

def is_parallel_sphinx(version):
    if version in [ '1.2b1-xgen', '1.2b2', '1.2b3', '1.2']:
        return True

    return False

def get_sphinx_args(sconf, conf):
    o = []

    o.append(get_tags(sconf.builder, sconf))
    o.append('-q')
    o.append('-b {0}'.format(sconf.builder))

    if (is_parallel_sphinx(pkg_resources.get_distribution("sphinx").version) and
        conf.project.name != 'mms'):
        o.append(' '.join( [ '-j', str(cpu_count() + 1) ]))

    o.append(' '.join( [ '-c', conf.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

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

#################### Public Fabric Tasks ####################

## modifiers

@task
def prereq():
    "Omnibus operation that builds all prerequisites for a Sphinx build."

    conf = lazy_conf()

    build_prerequisites(conf)

def build_prereq_jobs(conf):
    jobs = [
        {
            'job': generate.robots_txt_builder,
            'args': [ os.path.join( conf.paths.projectroot,
                                    conf.paths.public,
                                    'robots.txt'),
                      conf
                    ]
        },
        {
            'job': generate.write_include_index,
            'args': [conf]
        }
    ]

    for job in jobs:
        yield job


def build_prerequisites(conf):
    jobs = itertools.chain(process.manpage_jobs(conf),
                           build_prereq_jobs(conf),
                           generate.table_jobs(conf),
                           generate.api_jobs(conf),
                           generate.toc_jobs(conf),
                           generate.option_jobs(conf),
                           generate.steps_jobs(conf),
                           generate.release_jobs(conf),
                           intersphinx_jobs(conf),
                           generate.image_jobs(conf)
        )

    try:
        res = runner(jobs)
        print('[sphinx-prep]: built {0} pieces of content'.format(len(res)))
    except PoolResultsError:
        print('[WARNING]: sphinx prerequisites encountered errors. '
              'See output above. Continuing as a temporary measure.')

    generate.buildinfo_hash(conf)
    if conf.project.name != 'mms':
        # we copy source manually for mms in makefile.mms, avoiding this
        # operation to clarify the artifacts directory
        generate.source(conf)

    puts('[sphinx-prep]: resolving all intra-source dependencies now. (takes several seconds)')
    dep_count = process.refresh_dependencies(conf)
    puts('[sphinx-prep]: bumped timestamps of {0} files'.format(dep_count))

    with quiet():
        local(build_platform_notification('Sphinx', 'Build in progress past critical phase.'))

    puts('[sphinx-prep]: INFO - Build in progress past critical phase.')

    dump_file_hashes(conf.system.dependency_cache, conf)
    puts('[sphinx-prep]: build environment prepared for sphinx.')

def compute_sphinx_config(builder, sconf, conf):
    if 'inherit' in sconf[builder]:
        computed_config = sconf[sconf[builder]['inherit']]
        computed_config.update(sconf[builder])
    else:
        computed_config = sconf[builder]

    if conf.project.name == 'mms':
        computed_config.builder = builder.split('-')[0]
        if 'edition' not in computed_config:
            raise Exception('[sphinx] [error]: mms builds must have an edition.')
    else:
        computed_config.builder = builder
        computed_config.edition = None

    return computed_config

@task
def build(builder='html', conf=None):
    "Build a single sphinx target. Does not build prerequisites."

    conf = lazy_conf(conf)

    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.paths.projectroot,
                                                      conf.paths.builddata))

    build_worker_wrapper(builder, sconf, conf)

def build_worker_wrapper(builder, sconf, conf):
    sconf = compute_sphinx_config(builder, sconf, conf)

    build_worker(builder, sconf, conf)

def build_worker(builder, sconf, conf):
    conf = edition_setup(sconf.edition, conf)

    dirpath = os.path.join(conf.paths.branch_output, builder)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        puts('[{0}]: created {1}/{2}'.format(builder, conf.paths.branch_output, builder))

    puts('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

    cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {1}/{2}' # per-builder-doctreea
    sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                            conf.paths.branch_output,
                            builder,
                            conf.paths.branch_source)

    out = local(sphinx_cmd, capture=True)
    # out = sphinx_native_worker(sphinx_cmd)

    with settings(host_string=''):
        out = '\n'.join( [ out.stderr, out.stdout ] )
        output_sphinx_stream(out, builder, conf)

    puts('[build]: completed {0} build at {1}'.format(builder, timestamp()))

    finalize_build(builder, sconf, conf)

def sphinx_native_worker(sphinx_cmd):
    # Calls sphinx directly rather than in a subprocess/shell. Not used
    # currently because of the effect on subsequent multiprocessing pools.

    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    sp_cmd = __import__('sphinx.cmdline')

    sphinx_argv = sphinx_cmd.split()

    with swap_streams(StringIO()) as _out:
        r = sp_cmd.main(argv=sphinx_argv)
        out = _out.getvalue()

    if r != 0:
        exit(r)
    else:
        return r

def output_sphinx_stream(out, builder, conf=None):
    if conf is None:
        conf = lazy_conf()

    out = out.split('\n')
    out = list(set(out))

    out.sort()

    full_path = os.path.join(conf.paths.projectroot, conf.paths.branch_output)

    regx = re.compile(r'(.*):[0-9]+: WARNING: duplicate object description of ".*", other instance in (.*)')

    for l in out:
        if l == '':
            continue

        if builder.startswith('epub'):
            if l.startswith('WARNING: unknown mimetype'):
                continue
            elif len(l) == 0:
                continue
            elif l.startswith('WARNING: search index'):
                continue
            elif l.endswith('source/reference/sharding-commands.txt'):
                continue

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                continue

        if l.startswith(conf.paths.branch_output):
            l = os.path.join(conf.paths.projectroot, l[len(conf.paths.branch_output)+1:])
        elif l.startswith(full_path):
            l = os.path.join(conf.paths.projectroot, l[len(full_path)+1:])
        elif l.startswith('source'):
            l = os.path.join(conf.paths.projectroot, l)

        print(l)

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
            { 'job': puts,
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
    local('rsync -a {source}/ {destination}'.format(source=pjoin(conf.paths.projectroot,
                                                                 conf.paths.branch_output,
                                                                 builder),
                                                    destination=dest))

    puts('[{0}]: migrated build to {1}'.format(builder, dest))

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
        puts('[dirhtml] [clean]: removed excluded files from output directory')
