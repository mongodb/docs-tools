import os

from rstcloth.hash import generate_hash_file


#################### BuildInfo Hash ####################

def buildinfo_hash(conf):
    fn = os.path.join(conf.paths.projectroot,
                      conf.paths.includes,
                      'hash.rst')

    generate_hash_file(fn)

    release_fn = os.path.join(conf.paths.projectroot,
                              conf.paths.public_site_output,
                              'release.txt')

    release_root = os.path.dirname(release_fn)
    if not os.path.exists(release_root):
        os.makedirs(release_root)

    with open(release_fn, 'w') as f:
        f.write(conf.git.commit)

    print('[build]: generated "{0}" with current release hash.'.format(release_fn))
