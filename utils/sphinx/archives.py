import os.path

from utils.files import copy_if_needed, create_link, tarball

def html_tarball(builder, conf):
    copy_if_needed(os.path.join(conf.paths.projectroot,
                                conf.paths.includes, 'hash.rst'),
                   os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output,
                                'html', 'release.txt'))

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    tarball(name=tarball_name,
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
    tarball(name=tarball_name,
            path='man',
            cdir=os.path.dirname(basename),
            sourcep='man',
            newp=conf.project.name + '-manpages')

    copy_if_needed(tarball_name,
                   os.path.join(conf.paths.projectroot,
                                conf.paths.public_site_output,
                                os.path.basename(tarball_name)))

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        'manpages' + '.tar.gz'))
