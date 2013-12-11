import os.path
import re
import sys
import tarfile

from utils import ingest_yaml_list, ingest_yaml, expand_tree, dot_concat, hyph_concat
from fabric.api import task, puts, local, env, quiet, settings
from docs_meta import render_paths, get_conf, load_conf
from make import check_dependency, runner

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'bin')))
from htaccess import generate_redirects, process_redirect
from rstcloth.param import generate_params
from rstcloth.toc import CustomTocTree, AggregatedTocTree
from rstcloth.table import TableBuilder, YamlTable, ListTable, RstTable
from rstcloth.images import generate_image_pages
from rstcloth.releases import generate_release_output, generate_release_copy, generate_release_untar
from rstcloth.hash import generate_hash_file
from rstcloth.steps import render_step_file

#################### API Param Table Generator ####################

### Internal Method

def _generate_api_param(source, target, conf):
    r = generate_params(ingest_yaml_list(source), source, conf)
    r.write(target)

    puts('[api]: rebuilt {0}'.format(target))

### User facing fabric task

@task
def api():
    count = runner( api_jobs() )

    puts('[api]: generated {0} tables for api items'.format(count))

def api_jobs(conf=None):
    if conf is None:
        conf = get_conf()

    for source in expand_tree(os.path.join(conf.build.paths.projectroot, conf.build.paths.source, 'reference'), 'yaml'):
        target = dot_concat(os.path.splitext(source)[0], 'rst')

        yield {
                'target': target,
                'dependency': source,
                'job': _generate_api_param,
                'args': [source, target, conf]
              }

#################### Table of Contents Generator ####################

### Internal Methods

def _get_toc_base_name(fn):
    bn = os.path.basename(fn)

    if bn.startswith('ref-toc-'):
        return os.path.splitext(bn)[0][8:]
    elif bn.startswith('toc-') or bn.startswith('ref-spec-'):
        return os.path.splitext(bn)[0][4:]

def _get_toc_output_name(name, type, paths):
    if type == 'toc':
        return os.path.join(paths.includes, 'toc', '{0}.rst'.format(name))
    else:
        return os.path.join(paths.includes, 'toc', '{0}-{1}.rst'.format(type, name))

def _generate_toc_tree(fn, fmt, base_name, paths):
    puts('[toc]: generating {0} toc'.format(fn))
    if fmt == 'spec':
        spec = True
        toc = AggregatedTocTree(fn)
        fmt = toc._first_source[0:3]
        toc.build_dfn()
        toc.build_table()
        toc.finalize()

        if fmt == 'ref':
            if toc.table is not None:
                outfn = _get_toc_output_name(base_name, 'table', paths)
                t = TableBuilder(RstTable(toc.table))
                t.write(outfn)
                puts('[toc-spec]: wrote: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            puts('[toc-spec]: wrote: '  + outfn)

    else:
        spec = False
        toc = CustomTocTree(fn)
        toc.build_contents()

        if fmt == 'toc':
            toc.build_dfn()
        elif fmt == 'ref':
            toc.build_table()

        toc.finalize()

        outfn = _get_toc_output_name(base_name, 'toc', paths)
        toc.contents.write(outfn)
        puts('[toc]: wrote: '  + outfn)

        if fmt == 'ref':
            outfn = _get_toc_output_name(base_name, 'table', paths)
            t = TableBuilder(RstTable(toc.table))
            t.write(outfn)
            puts('[ref-toc]: wrote: '  + outfn)
        elif fmt == 'toc':
            outfn = _get_toc_output_name(base_name, 'dfn-list', paths)
            toc.dfn.write(outfn)
            puts('[toc]: wrote: '  + outfn)

    puts('[toc]: compiled toc output for {0}'.format(fn))

### User facing fabric task

@task
def toc():
    count = runner( toc_jobs() )

    puts('[toc]: built {0} tables of contents'.format(count))

def toc_jobs():
    paths = render_paths('obj')

    for fn in expand_tree(paths.includes, 'yaml'):
        if fn.startswith(os.path.join(paths.includes, 'table')):
            continue
        elif fn.startswith(os.path.join(paths.includes, 'step')):
            continue
        elif len(fn) >= 24:
            base_name = _get_toc_base_name(fn)

            fmt = fn[20:24]
            if fmt != 'spec':
                fmt = fn[16:19]

            o = {
                  'dependency': fn,
                  'job': _generate_toc_tree,
                  'target': [],
                  'args': [fn, fmt, base_name, paths]
                }

            if fmt != 'spec':
                o['target'].append(_get_toc_output_name(base_name, 'toc', paths))

            is_ref_spec = fn.startswith(os.path.join(os.path.dirname(fn), 'ref-spec'))

            if not is_ref_spec and (fmt == 'toc' or fmt == 'spec'):
                o['target'].append(_get_toc_output_name(base_name, 'dfn-list', paths))
            elif fmt == 'ref' or is_ref_spec:
                o['target'].append(_get_toc_output_name(base_name, 'table', paths))

            yield o

#################### Table Builder ####################

## Internal Supporting Methods

def _get_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return dot_concat(os.path.join(base, 'table', leaf[6:]), 'rst')

def _get_list_table_output_name(fn):
    base, leaf = os.path.split(os.path.splitext(fn)[0])

    return dot_concat(hyph_concat(os.path.join(base, 'table', leaf[6:]), 'list'), 'rst')

def make_parent_dirs(*paths):
    for path in paths:
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

def _generate_tables(source, target, list_target):
    table_data = YamlTable(source)

    make_parent_dirs(target, list_target)

    # if not table_data.format or table_data.format is None:
    #     build_all = True

    list_table = TableBuilder(ListTable(table_data))
    list_table.write(list_target)
    puts('[table]: rebuilt {0}'.format(list_target))

    list_table.write(target)
    puts('[table]: rebuilt {0} as (a list table)'.format(target))

    # if build_all or table_data.format == 'list':
    #     list_table = TableBuilder(ListTable(table_data))
    #     list_table.write(list_target)
    #     puts('[table]: rebuilt {0}'.format(list_target))
    # if build_all or table_data.format == 'rst':
    #     # this really ought to be RstTable, but there's a bug there.
    #     rst_table = TableBuilder(ListTable(table_data))
    #     rst_table.write(target)

    #     puts('[table]: rebuilt {0} as (a list table)'.format(target))

    puts('[table]: rebuilt table output for {0}'.format(source))

## User facing fabric task

@task
def tables():
    count = runner( table_jobs() )

    puts('[table]: built {0} tables'.format(count))

def table_jobs():
    paths = get_conf().build.paths

    for source in expand_tree(os.path.join(paths.projectroot, paths.includes), 'yaml'):
        if os.path.basename(source).startswith('table'):
            target = _get_table_output_name(source)
            list_target = _get_list_table_output_name(source)

            yield {
                    'target': [ target, list_target ],
                    'dependency': source,
                    'job': _generate_tables,
                    'args': [ source, target, list_target ]
                  }


#################### Generate Images and Related Content  ####################

## Internal Supporting Methods

def _get_inkscape_cmd():
    if sys.platform in ['linux', 'linux2']:
        return '/usr/bin/inkscape'
    elif sys.platform == 'darwin':
        inkscape = '/Applications/Inkscape.app/Contents/Resources/bin/inkscape'
        if os.path.exists(inkscape):
            return inkscape

    return 'inkscape'

def _generate_images(cmd, dpi, width, target, source):
    local(cmd.format(cmd=_get_inkscape_cmd(),
                     dpi=dpi,
                     width=width,
                     target=target,
                     source=source))
    puts('[image]: generated image file  {0}'.format(source))


## User facing fabric task

@task
def images():
    count = runner( image_jobs() )
    puts('[image]: rebuilt {0} rst and image files'.format(count))

def image_jobs():
    conf = get_conf()
    paths = conf.build.paths

    meta_file = os.path.join(paths.images, 'metadata') + '.yaml'

    if not os.path.exists(meta_file):
        return

    images_meta = ingest_yaml_list(meta_file)

    for image in images_meta:
        image['dir'] = paths.images
        source_base = os.path.join(image['dir'], image['name'])
        source_file = source_base + '.svg'
        rst_file = source_base + '.rst'
        image['conf'] = conf

        yield {
                'target': rst_file,
                'dependency': [ meta_file, os.path.join(paths.buildsystem, 'rstcloth', 'images.py') ],
                'job': generate_image_pages,
                'args': image
              }

        for output in image['output']:
            if 'tag' in output:
                tag = '-' + output['tag']
            else:
                tag = ''

            target_img = source_base + tag + '.png'

            inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 0.0 -e >/dev/null {target} {source}'

            yield {
                    'target': target_img,
                    'dependency': source_file,
                    'job': _generate_images,
                    'args': [
                              inkscape_cmd,
                              output['dpi'],
                              output['width'],
                              target_img,
                              source_file
                            ],
                  }


#################### Snippets for Inclusion in Installation Guides  ####################

# generate_release_output(builder, platform, version, release)

def _check_release_dependency(target):
    if env.FORCE:
        return True
    elif check_dependency(target, os.path.join(conf.build.paths.projectroot, 'conf.py')):
        return True
    elif check_dependency(target, os.path.join(conf.build.paths.projectroot,
                                               conf.build.paths.buildsystem,
                                               'rstcloth', 'releases.py')):
        return True
    else:
        return False

def _generate_release_ent(rel, target, release):
    r = generate_release_output( rel['type'], rel['type'].split('-')[0], rel['system'], release )
    r.write(target)
    puts('[release]: wrote: ' + target)

def _generate_release_core(rel, target, release):
    r = generate_release_output( rel, rel.split('-')[0], 'core', release )
    r.write(target)
    puts('[release]: wrote: ' + target)

def _generate_untar_core(rel, target, release):
    r = generate_release_untar(rel, release)
    r.write(target)
    puts('[release]: wrote: ' + target)

def _generate_copy_core(rel, target, release):
    r = generate_release_copy(rel, release)
    r.write(target)
    puts('[release]: wrote: ' + target)

@task
def releases():
    count = runner( release_jobs() )
    puts('[releases]: completed regenerating {0} release files.'.format(count))

def release_jobs(conf=None):
    if conf is None:
        conf = get_conf()
    data_file = os.path.join(conf.build.paths.builddata, 'releases') + '.yaml'

    if 'release' in conf.version:
        release_version = conf.version.release
    else:
        release_version = conf.version.published[0]

    if not os.path.exists(data_file):
        return

    rel_data = ingest_yaml(os.path.join(conf.build.paths.builddata, 'releases') + '.yaml')

    deps = [ os.path.join(conf.build.paths.projectroot, 'conf.py'),
             os.path.join(conf.build.paths.projectroot,
                          conf.build.paths.buildsystem,
                          'rstcloth', 'releases.py') ]

    for rel in rel_data['source-files']:
        target = os.path.join(conf.build.paths.projectroot,
                              conf.build.paths.includes,
                              'install-curl-release-{0}.rst'.format(rel))

        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_release_core,
                'args': [ rel, target, release_version ]
              }

        target = os.path.join(conf.build.paths.projectroot,
                              conf.build.paths.includes,
                              'install-untar-release-{0}.rst'.format(rel))
        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_untar_core,
                'args': [ rel, target, release_version ]
              }

        target = os.path.join(conf.build.paths.projectroot,
                              conf.build.paths.includes,
                              'install-copy-release-{0}.rst'.format(rel))
        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_copy_core,
                'args': [ rel, target, release_version ]
              }

    for rel in rel_data['subscription-build']:
        target = 'source/includes/install-curl-release-ent-{0}.rst'.format(rel['system'])

        yield {
                'target': target,
                'dependency': deps,
                'job': _generate_release_ent,
                'args': [ rel, target, release_version ]
              }


#################### Copy of Source Directory for Build  ####################

@task
def source(conf=None):
    if conf is None:
        conf = get_conf()

    target = os.path.join(conf.build.paths.projectroot, conf.build.paths.branch_output)

    if not os.path.exists(target):
        os.makedirs(target)
        puts('[sphinx-prep]: created ' + target)
    elif not os.path.isdir(target):
        abort('[sphinx-prep]: {0} exists and is not a directory'.format(target))

    source_dir = os.path.join(conf.build.paths.projectroot, conf.build.paths.source)

    local('rsync --checksum --recursive --delete {0} {1}'.format(source_dir, target))
    puts('[sphinx-prep]: updated source in {0}'.format(target))

#################### Generate the Sitemap ####################

@task
def sitemap(config_path=None):
    paths = render_paths('obj')

    sys.path.append(os.path.join(paths.projectroot, paths.buildsystem, 'bin'))
    import sitemap_gen

    if config_path is None:
        config_path = os.path.join(paths.projectroot, 'conf-sitemap.xml')

    if not os.path.exists(config_path):
        puts('[ERROR] [sitemap]: configuration file {0} does not exist. Returning early'.fomrat(config_path))
        return False

    sitemap = sitemap_gen.CreateSitemapFromFile(configpath=config_path,
                                                suppress_notify=True)
    if sitemap is None:
        puts('[ERROR] [sitemap]: failed to generate the sitemap due to encountered errors.')
        return False

    sitemap.Generate()

    puts('[sitemap]: generated sitemap according to the config file {0}'.format(config_path))
    return True

#################### BuildInfo Hash ####################

def buildinfo_hash(conf):
    fn = os.path.join(conf.build.paths.projectroot,
                      conf.build.paths.includes,
                      'hash.rst')

    generate_hash_file(fn)

    release_fn = os.path.join(conf.build.paths.projectroot,
                              conf.build.paths.public_site_output,
                              'release.txt')

    release_root = os.path.dirname(release_fn)
    if not os.path.exists(release_root):
        os.makedirs(release_root)

    with open(release_fn, 'w') as f:
        f.write(conf.git.commit)

    puts('[build]: generated "{0}" with current release hash.'.format(release_fn))

#################### tarball ####################

def tarball(name, path, sourcep=None, newp=None, cdir=None):
    tarball_path = os.path.dirname(name)
    if not os.path.exists(tarball_path):
        os.makedirs(tarball_path)

    with tarfile.open(name, 'w:gz') as t:
        if newp is not None:
            arcname = os.path.join(newp, os.path.basename(path))
        else:
            arcname = None

        if cdir is not None:
            path = os.path.join(cdir, path)

        t.add(name=path, arcname=arcname)

    puts('[tarball]: created {0}'.format(name))

#################### .htaccess files ####################

@task
def htaccess(fn='.htaccess'):
    conf = load_conf()

    if env.input_file is None:
        in_files = [i for i in expand_tree(conf.build.paths.builddata, 'yaml') if os.path.basename(i).startswith('htaccess')]
    else:
        in_files = list(env.input_file)

    sources = []
    for i in in_files:
        sources.extend(ingest_yaml_list(i))

    dirname = os.path.dirname(fn)
    if not dirname == '' and not os.path.exists(dirname):
        os.makedirs(dirname)

    lines = set( [ ] )

    for redir in sources:
        lines.add(generate_redirects(process_redirect(redir, conf), conf=conf, match=False))

    with open(fn, 'w') as f:
        f.writelines(lines)
        f.write('\n')
        f.writelines( ['<FilesMatch "\.(ttf|otf|eot|woff)$">','\n',
                       '   Header set Access-Control-Allow-Origin "*"', '\n'
                       '</FilesMatch>', '\n'] )


    puts('[redirect]: regenerated {0} with {1} redirects ({2} lines)'.format(fn, len(sources), len(lines)))

#################### steps ####################

def _get_steps_output_fn(fn, paths):
    root_name = os.path.splitext(os.path.basename(fn).split('-', 1)[1])[0] + '.rst'

    return os.path.join(paths.projectroot, paths.includes, 'steps', root_name)

def steps_jobs():
    paths = render_paths('obj')

    for fn in expand_tree(os.path.join(paths.projectroot, paths.includes), 'yaml'):
        if fn.startswith(os.path.join(paths.projectroot, paths.includes, 'step')):
            out_fn = _get_steps_output_fn(fn, paths)

            yield { 'dependency': fn,
                    'target': out_fn,
                    'job': render_step_file,
                    'args': [fn, out_fn] }

@task
def steps():
    count = runner( steps_jobs() )

    puts('[steps]: rendered {0} step files'.format(count))
