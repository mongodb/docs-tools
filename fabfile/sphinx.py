import datetime
import itertools
import os
import re
import pkg_resources
import sys

from fabric.api import cd, local, task, env, hide, settings, quiet
from fabric.utils import puts
from multiprocessing import cpu_count

from utils import ingest_yaml, expand_tree, swap_streams, hyph_concat, build_platform_notification, BuildConfiguration, AttributeDict
from clean import cleaner
from make import runner, dump_file_hashes
import generate
import process
import docs_meta
import mms

conf = docs_meta.get_conf()
paths = conf.build.paths

from intersphinx import intersphinx, intersphinx_jobs
intersphinx = task(intersphinx)

env.EDITION = None
@task
def edition(val=None):
    "Specify the edition for multi-edition outputs such as MMS."

    # this is a wrapper so we can use edition_setup elsewhere
    edition_setup(val, conf)

def edition_setup(val, conf):
    if val is None and env.EDITION is not None:
        val = env.EDITION
    else:
        env.EDITION = val

    return docs_meta.edition_setup(val, conf)

def get_tags(target, sconf):
    ret = []

    if target.startswith('html') or target.startswith('dirhtml'):
        ret.append('website')
    else:
        ret.append('print')

    if 'edition' in sconf:
        ret.append(sconf.edition)

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

    o.append(' '.join( [ '-c', conf.build.paths.projectroot ] ))

    if 'language' in sconf:
        o.append("-D language='{0}'".format(sconf.language))

    return ' '.join(o)

#################### Associated Sphinx Artifacts ####################

def html_tarball(builder, conf):
    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    process.copy_if_needed(os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.includes, 'hash.rst'),
                           os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.branch_output,
                                        'html', 'release.txt'))

    basename = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.public_site_output,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    generate.tarball(name=tarball_name,
                     path='html',
                     cdir=os.path.join(conf.build.paths.projectroot,
                                       conf.build.paths.branch_output),
                     sourcep='html',
                     newp=os.path.basename(basename))

    process.create_link(input_fn=os.path.basename(tarball_name),
                         output_fn=os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.public_site_output,
                                                conf.project.name + '.tar.gz'))

def man_tarball(conf):
    basename = os.path.join(conf.build.paths.projectroot,
                            conf.build.paths.branch_output,
                            'manpages-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'
    generate.tarball(name=tarball_name,
                     path='man',
                     cdir=os.path.dirname(basename),
                     sourcep='man',
                     newp=conf.project.name + '-manpages'
                     )

    process.copy_if_needed(tarball_name,
                           os.path.join(conf.build.paths.projectroot,
                                        conf.build.paths.public_site_output,
                                        os.path.basename(tarball_name)))

    process.create_link(input_fn=os.path.basename(tarball_name),
                         output_fn=os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.public_site_output,
                                                'manpages' + '.tar.gz'))

#################### Public Fabric Tasks ####################

## modifiers

@task
def prereq():
    "Omnibus operation that builds all prerequisites for a Sphinx build."

    conf = docs_meta.get_conf()

    build_prerequisites(conf)

def build_prereq_jobs(conf):
    jobs = [
        {
            'job': generate.robots_txt_builder,
            'args': [ os.path.join( conf.build.paths.projectroot,
                                    conf.build.paths.public,
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
    jobs = itertools.chain(process.manpage_jobs(),
                           build_prereq_jobs(conf),
                           generate.table_jobs(),
                           generate.api_jobs(conf),
                           generate.toc_jobs(),
                           generate.steps_jobs(),
                           generate.release_jobs(conf),
                           intersphinx_jobs(),
                           generate.image_jobs()
        )

    job_count = runner(jobs)
    puts('[sphinx-prep]: built {0} pieces of content'.format(job_count))

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

    dump_file_hashes(conf.build.system.dependency_cache, conf)
    puts('[sphinx-prep]: build environment prepared for sphinx.')

def compute_sphinx_config(builder, conf):
    sconf = BuildConfiguration(filename='sphinx.yaml',
                               directory=os.path.join(conf.build.paths.projectroot,
                                                      conf.build.paths.builddata))

    if conf.project.name == 'mms':
        builder, edition = builder.split('-')
    else:
        edition = None

    if builder in sconf:
        sphinx_target = sconf[builder]
    else:
        sphinx_target = AttributeDict()

    if 'inherit' in sphinx_target:
        computed_config = sconf[sphinx_target['inherit']]
        computed_config.update(sphinx_target)
    else:
        computed_config = sphinx_target

    if 'builder' not in computed_config:
        computed_config.builder = builder

    computed_config.edition = edition

    return computed_config

@task
def build(builder='html', conf=None):
    "Build a single sphinx target. Does not build prerequisites."

    if conf is None:
        conf = docs_meta.get_conf()

    build_worker(builder, conf)

def build_worker(builder, conf):
    sconf = compute_sphinx_config(builder, conf)
    conf = edition_setup(sconf.edition, conf)

    if conf.project.name == 'mms':
        conf = edition_setup(sconf.edition, conf)
    else:
        edition = None

    with settings(host_string='sphinx'):
        dirpath = os.path.join(conf.build.paths.branch_output, builder)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
            puts('[{0}]: created {1}/{2}'.format(builder, conf.build.paths.branch_output, builder))

        puts('[{0}]: starting {0} build {1}'.format(builder, timestamp()))

        cmd = 'sphinx-build {0} -d {1}/doctrees-{2} {3} {1}/{2}' # per-builder-doctreea
        sphinx_cmd = cmd.format(get_sphinx_args(sconf, conf),
                                conf.build.paths.branch_output,
                                builder,
                                conf.build.paths.branch_source)

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
        conf = get_conf()

    out = out.split('\n')
    out = list(set(out))

    out.sort()

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

        full_path = os.path.join(conf.build.paths.projectroot, conf.build.paths.branch_output)
        if l.startswith(conf.build.paths.branch_output):
            l = l[len(conf.build.paths.branch_output)+1:]
        elif l.startswith(full_path):
            l = l[len(full_path)+1:]

        f1 = regx.match(l)
        if f1 is not None:
            g = f1.groups()

            if g[1].endswith(g[0]):
                continue

        l = os.path.join(conf.build.paths.projectroot, l)

        print(l)

def finalize_build(builder, sconf, conf):
    if 'language' in sconf:
        # reinitialize conf and builders for internationalization
        conf.paths = docs_meta.render_paths(None, conf, sconf.language)
        builder = sconf.builder
        target = builder
    else:
        # mms compatibility
        target = builder
        builder = builder.split('-', 1)[0]

    jobs = {
        'linkcheck': [
            { 'job': puts,
              'args': ['[{0}]: See {1}/{0}/output.txt for output.'.format(builder, conf.build.paths.branch_output)]
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

    if conf.build.system.branched is True and conf.git.branches.current == 'master':
        jobs['all'].append(
            { 'job': generate.create_manual_symlink,
              'args': [conf]
            }
        )


    print('[sphinx] [post] [{0}]: running post-processing steps.'.format(builder))
    count = runner(itertools.chain(jobs[builder], jobs['all']), pool=1)
    print('[sphinx] [post] [{0}]: completed {1} post-processing steps'.format(builder, count))

#################### Sphinx Post-Processing ####################

def finalize_epub_build(conf):
    epub_name = '-'.join(conf.project.title.lower().split())
    epub_branched_filename = epub_name + '-' + conf.git.branches.current + '.epub'
    epub_src_filename = epub_name + '.epub'

    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    process.copy_if_needed(source_file=os.path.join(conf.build.paths.projectroot,
                                                    conf.build.paths.branch_output,
                                                    'epub', epub_src_filename),
                           target_file=os.path.join(conf.build.paths.projectroot,
                                                    conf.build.paths.public_site_output,
                                                    epub_branched_filename))
    process.create_link(input_fn=epub_branched_filename,
                         output_fn=os.path.join(conf.build.paths.projectroot,
                                                conf.build.paths.public_site_output,
                                                epub_src_filename))


def get_single_html_dir(conf):
    return os.path.join(conf.build.paths.public_site_output, 'single')

def finalize_single_html_jobs(builder, conf):
    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        raise StopIteration

    pjoin = os.path.join

    single_html_dir = get_single_html_dir(conf)

    if not os.path.exists(single_html_dir):
        os.makedirs(single_html_dir)

    try:
        process.manual_single_html(input_file=pjoin(conf.build.paths.branch_output,
                                                    builder, 'contents.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    except (IOError, OSError):
        process.manual_single_html(input_file=pjoin(conf.build.paths.branch_output,
                                                    builder, 'index.html'),
                                   output_file=pjoin(single_html_dir, 'index.html'))
    process.copy_if_needed(source_file=pjoin(conf.build.paths.branch_output,
                                             builder, 'objects.inv'),
                           target_file=pjoin(single_html_dir, 'objects.inv'))

    single_path = pjoin(single_html_dir, '_static')

    for fn in expand_tree(pjoin(conf.build.paths.branch_output,
                                builder, '_static'), None):

        yield {
            'job': process.copy_if_needed,
            'args': [fn, pjoin(single_path, os.path.basename(fn))],
            'target': None,
            'dependency': None
        }

def finalize_dirhtml_build(builder, conf):
    pjoin = os.path.join

    process.error_pages()

    single_html_dir = get_single_html_dir(conf)
    search_page = pjoin(conf.build.paths.branch_output, builder, 'index.html')

    if conf.project.name == 'mms' and mms.should_migrate(builder, conf) is False:
        return False

    if os.path.exists(search_page):
        process.copy_if_needed(source_file=search_page,
                               target_file=pjoin(single_html_dir, 'search.html'))

    dest = pjoin(conf.build.paths.projectroot, conf.build.paths.public_site_output)
    local('rsync -a {source}/ {destination}'.format(source=pjoin(conf.build.paths.projectroot,
                                                                 conf.build.paths.branch_output,
                                                                 builder),
                                                    destination=dest))

    puts('[{0}]: migrated build to {1}'.format(builder, dest))

    if conf.git.branches.current in conf.git.branches.published:
        sitemap_exists = generate.sitemap()

        if sitemap_exists is True:
            process.copy_if_needed(source_file=pjoin(conf.build.paths.projectroot,
                                                     conf.build.paths.branch_output,
                                                     'sitemap.xml.gz'),
                                   target_file=pjoin(conf.build.paths.projectroot,
                                                     conf.build.paths.public_site_output,
                                                     'sitemap.xml.gz'))

    sconf = BuildConfiguration('sphinx.yaml', pjoin(conf.build.paths.projectroot,
                                                conf.build.paths.builddata))

    if 'dirhtml' in sconf and 'excluded_files' in sconf.dirhtml:
        fns = [ pjoin(conf.build.paths.projectroot,
                      conf.build.paths.public_site_output,
                      fn)
                for fn in sconf.dirhtml.excluded_files ]

        cleaner(fns)
        puts('[dirhtml] [clean]: removed excluded files from output directory')
