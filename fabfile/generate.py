import os.path
import sys
import re

from multiprocessing import Pool
from utils import ingest_yaml_list, ingest_yaml, expand_tree, dot_concat, hyph_concat, build_platform_notification
from fabric.api import task, puts, local, env, quiet
from make import check_dependency, check_multi_dependency
from docs_meta import render_paths

paths = render_paths('dict')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'])))
from rstcloth.param import generate_params
from rstcloth.toc import CustomTocTree, AggregatedTocTree
from rstcloth.table import TableBuilder, YamlTable, ListTable, RstTable
from rstcloth.images import generate_image_pages
from rstcloth.releases import generate_release_output

#################### API Param Table Generator ####################

### Internal Method

def _generate_api_param(source, target):
    r = generate_params(ingest_yaml_list(source))
    r.write(target)

    puts('[api]: rebuilt {0}'.format(target))

### User facing fabric task

@task
def api():
    p = Pool()

    count = 0
    for source in expand_tree('source/reference', 'yaml'):
        target = dot_concat(os.path.splitext(source)[0], 'rst')
        if env.FORCE or check_dependency(target, source):
            # _generate_api_param(source, target)
            p.apply_async(_generate_api_param, args=(source, target))

            count +=1

    p.close()
    p.join()
    puts('[api]: generated {0} tables for api items'.format(count))

#################### Table of Contents Generator ####################

### Internal Methods

def _get_toc_base_name(fn):
    bn = os.path.basename(fn)

    if bn.startswith('ref-toc-'):
        return os.path.splitext(bn)[0][8:]
    if bn.startswith('toc-'):
        return os.path.splitext(bn)[0][4:]

def _get_toc_output_name(name, type):
    return 'source/includes/{0}-{1}.rst'.format(type, name)

def _generate_toc_tree(fn, fmt, base_name):
    if fmt == 'spec': 
        spec = True
        toc = AggregatedTocTree(fn)
        toc.build_dfn()
        toc.build_table()
        toc.finalize()
    else:
        spec = False
        toc = CustomTocTree(fn)
        toc.build_contents()
        
        if fmt == 'toc':
            toc.build_dfn()
        elif fmt == 'ref':
            toc.build_table()

        toc.finalize()

        outfn = _get_toc_output_name(base_name, 'toc')
        toc.contents.write(outfn)
        puts('[toc]: wrote: '  + outfn)

    if spec is True or fmt == 'toc':
        outfn = _get_toc_output_name(base_name, 'dfn-list')
        toc.dfn.write(outfn)
        puts('[toc]: wrote: '  + outfn)
    elif spec is True or fmt == 'ref':
        if toc.table is not None:
            outfn = _get_toc_output_name(base_name, 'table')
            t = TableBuilder(RstTable(toc.table))
            t.write(outfn)
            puts('[toc]: wrote: '  + outfn)

    puts('[toc]: complied toc output for {0}'.format(fn))

### User facing fabric task

@task
def toc():
    p = Pool()

    count = 0
    for fn in expand_tree('source/includes', 'yaml'):

        if fn.startswith('source/includes/table'):
            pass
        elif len(fn) >= 24:
            base_name = _get_toc_base_name(fn)

            fmt = fn[20:24]
            if fmt != 'spec':
                fmt = fn[16:19]

            outputs = [ _get_toc_output_name(i[0], i[1]) for i in [(base_name, 'dfn-list'), 
                                                                   (base_name, 'toc')] ]

            if env.FORCE or check_multi_dependency(outputs, fn):
                print base_name
                _generate_toc_tree(fn, fmt, base_name)
                #p.apply_async(_generate_toc_tree, args=(fn, fmt, base_name))
                count += 1

    p.close()
    p.join()

    puts('[toc]: built {0} tables of contents'.format(count))

#################### Table Builder ####################

## Internal Supporting Methods

def _get_table_output_name(fn):
    return dot_concat(os.path.splitext(fn)[0], 'rst')
def _get_list_table_output_name(fn):
    return dot_concat(hyph_concat(os.path.splitext(fn)[0], 'list'), 'rst')

def _generate_tables(source, target, list_target):
    table_data = YamlTable(source)

    build_all = False
    if not table_data.format or table_data.format is None:
        build_all = True

    if build_all or table_data.format == 'list':
        list_table = TableBuilder(ListTable(table_data))
        list_table.write(list_target)
        puts('[table]: rebuilt {0}'.format(list_target))

        list_table.write(target)
        puts('[table]: rebuilt {0} as (a list table)'.format(target))

    # if build_all or table_data.format == 'rst':
    #     # this really ought to be RstTable, but there's a bug there.
    #     rst_table = TableBuilder(ListTable(table_data))
    #     rst_table.write(target)

    #     puts('[table]: rebuilt {0} as (a list table)'.format(target))

    puts('[table]: rebuilt table output for {0}'.format(source))

## User facing fabric task

@task
def tables():
    p = Pool()

    count = 0
    for source in expand_tree(paths['includes'], 'yaml'):
        if os.path.basename(source).startswith('table'):

            target = _get_table_output_name(source)
            list_target = _get_list_table_output_name(source)

            if env.FORCE or check_dependency(target, source) or check_dependency(list_target, source):
                # _generate_tables(source, target, list_target)
                p.apply_async(_generate_tables, args=(source, target, list_target))
                count += 1

    p.close()
    p.join()

    puts('[table]: built {0} tables'.format(count))

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
    meta_file = os.path.join(paths['images'], 'metadata') + '.yaml'
    images_meta = ingest_yaml_list(meta_file)

    p = Pool()

    count_rst = 0
    count_png = 0
    for image in images_meta:
        image['dir'] = paths['images']
        source_base = os.path.join(image['dir'], image['name'])
        source_file = source_base + '.svg'
        rst_file = source_base + '.rst'


        if env.FORCE or ( check_dependency(rst_file, meta_file) and
                          check_dependency(rst_file, os.path.join(paths['buildsystem'], 'rstcloth', 'images.py'))):
            p.apply_async(generate_image_pages, kwds=image)
            count_rst += 1

        for output in image['output']:
            if 'tag' in output:
                tag = '-' + output['tag']
            else:
                tag = ''

            target_img = source_base + tag + '.png'

            if env.FORCE or check_dependency(target_img, source_file):
                inkscape_cmd = '{cmd} -z -d {dpi} -w {width} -y 0.0 -e >/dev/null {target} {source}'
                # _generate_images(inkscape_cmd, output['dpi'], output['width'], target_img, source_file)
                p.apply_async(_generate_images, args=(inkscape_cmd, output['dpi'], output['width'], target_img, source_file))

                count_png += 1

    p.close()
    p.join()
    puts('[image]: rebuilt {0} rst files and {1} image files'.format(count_rst, count_png))

#################### Snippets for Inclusion in Installation Guides  ####################

# generate_release_output(builder, platform, version, release)

def _check_release_dependency(target):
    if env.FORCE:
        return True
    elif check_dependency(target, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'conf.py')):
        return True
    elif check_dependency(target, os.path.join(os.path.dirname(__file__), '..', 'rstcloth', 'releases.py')):
        return True
    else:
        return False

def _generate_release_ent(rel):
    target = 'source/includes/install-curl-release-ent-{0}.rst'.format(rel['system'])

    if _check_release_dependency(target):
        r = generate_release_output(rel['type'], rel['type'].split('-')[0], rel['system'] )
        r.write(target)
        puts('[release]: wrote: ' + target)

def _generate_release_core(rel):
    target = 'source/includes/install-curl-release-{0}.rst'.format(rel)
    if _check_release_dependency(target):
        r = generate_release_output(rel, rel.split('-')[0], 'core' )
        r.write(target)
        puts('[release]: wrote: ' + target)

@task
def releases():
    rel_data = ingest_yaml(os.path.join(paths['builddata'], 'releases') + '.yaml')

    p = Pool()
    for rel in rel_data['source-files']:
        p.apply_async(_generate_release_core, args=[rel])

    for rel in rel_data['subscription-build']:
        p.apply_async(_generate_release_ent, args=[rel])

    p.close()
    p.join()
    puts('[releases]: completed regenerating release files.')

#################### Copy of Source Directory for Build  ####################

@task
def source():
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['branch-output']))

    if not os.path.exists(target):
        os.makedirs(target)
        puts('[sphinx-prep]: created ' + target)
    elif not os.path.isdir(target):
        abort('[sphinx-prep]: {0} exists and is not a directory'.format(target))

    local('rsync --recursive --times --delete {0} {1}'.format(paths['source'], target))
    puts('[sphinx-prep]: updated source in {0}'.format(target))

    with quiet():
        local(build_platform_notification('Sphinx', 'Build in progress past critical phase.'))

    puts('[sphinx-prep]: INFO - Build in progress past critical phase.')

#################### Generate the Sitemap ####################

@task
def sitemap(config_path=None):
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', paths['buildsystem'], 'bin')))
    import sitemap_gen

    if config_path is None:
        config_path = 'conf-sitemap.xml'

    sitemap = sitemap_gen.CreateSitemapFromFile(configpath=config_path,
                                                suppress_notify=True)
    sitemap.Generate()

    puts('[sitemap]: generated sitemap according to the config file {0}'.format(config_path))
