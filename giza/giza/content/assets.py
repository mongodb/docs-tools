import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from giza.git import GitRepo

def assets_setup(path, branch, repo):
    if os.path.exists(path):
        g = GitRepo(path)
        g.pull(branch=branch)
        logger.info('updated {0} repository'.format(path))
    else:
        base, name = os.path.split(path)

        g = GitRepo(base)

        g.clone(repo, repo_path=name, branch=branch)
        logger.info('cloned {0} branch from repo {1}'.format(branch, repo))
