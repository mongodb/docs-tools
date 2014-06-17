import os.path

from giza.tools.files import copy_if_needed, create_link, tarball

def html_tarball(builder, conf):
    copy_if_needed(os.path.join(conf.paths.projectroot,
                                conf.paths.includes, 'hash.rst'),
                   os.path.join(conf.paths.projectroot,
                                conf.paths.branch_output,
                                builder, 'release.txt'))

    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            conf.project.name + '-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'

    tarball(name=tarball_name,
            path=builder,
            cdir=os.path.join(conf.paths.projectroot,
                              conf.paths.branch_output),
            newp=os.path.basename(basename))

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        conf.project.name + '.tar.gz'))

def man_tarball(builder, conf):
    basename = os.path.join(conf.paths.projectroot,
                            conf.paths.public_site_output,
                            'manpages-' + conf.git.branches.current)

    tarball_name = basename + '.tar.gz'
    tarball(name=tarball_name,
            path=builder,
            cdir=os.path.join(conf.paths.projectroot, conf.paths.branch_output),
            newp=conf.project.name + '-manpages')

    create_link(input_fn=os.path.basename(tarball_name),
                 output_fn=os.path.join(conf.paths.projectroot,
                                        conf.paths.public_site_output,
                                        'manpages' + '.tar.gz'))
