from fabric.api import local, hide, lcd, puts, settings, hide
import fabric.state
import os
import sys
import argparse

fabric.state.output.running = False

build = 'build'
repo_path = os.path.join(build, 'checkout')

def bootstrap_test_env(repo):
    if not os.path.exists(build):
        os.mkdir(build)

    if not os.path.exists(repo_path):
        local('git clone {0} {1}'.format(repo, repo_path))
    else:
        if local('git remote show origin | grep "{0}" | wc -l'.format(repo), capture=True) > 1:
            with lcd(repo_path):
                local('git fetch origin')
        else:
            local('rm -rf ' + repo_path)
            local('git clone {0} {1}'.format(repo, repo_path))

def setup_docs_tools_repo():
    build_path = os.path.join(repo_path, 'build') 
    if not os.path.exists(build_path):
        os.makedirs(build_path)

    with lcd(build_path):
        if os.path.exists(os.path.join(repo_path, 'build', 'docs-tools')):
            with lcd('docs-tools'):
                local('git reset --hard HEAD~2')
                local('git pull')
        else:
            local('git clone ../../../.git docs-tools')

def get_branch_list():
    with lcd(repo_path):
        branches = local('git branch -r --no-color --no-column', capture=True).stdout.split()
        branches = [ branch.split('/', 1)[1] for branch in set(branches) if len(branch.split('/', 1)) > 1 and not branch.split('/', 1)[1] == 'HEAD' ]
    return branches

def build_target(target, flags):
    local( ' '.join([ 'make', flags, target ] ) )

def run_prep(builders, flags):
    from multiprocessing import Pool
    workers = len(builders)
    p = Pool(processes=workers)

    for builder in builders:
        p.apply_async(build_target, (builder, flags))

    p.close()
    p.join()

    puts('[test]: rebuilt "{0}" using {1} workers, first.'.format(', '.join(builders), workers))


def run_tests(branch):
    with lcd(repo_path):
        if local('git symbolic-ref HEAD', capture=True).rsplit('/', 1)[1] != branch:
            local('git branch -f {0} origin/{0}'.format(branch))
        local('git reset --hard HEAD~2')
        local('git checkout {0}'.format(branch))
        local('git pull')

    mflags = 'MAKEFLAGS=-r --no-print-directory'
    if sys.platform.startswith('linux'):
        mflags += ' -j'
    elif sys.platform.startswith('darwin'):
        mflags += ' -j16'

    with lcd(repo_path):
        local('python bootstrap.py')
        puts('[test]: repository bootstrapped in branch: {0}'.format(branch))
        puts('------------------------------------------------------------------------')
        run_prep(['json', 'texinfo', 'dirhtml'], mflags)
        puts('------------------------------------------------------------------------')
        local('make {0} publish'.format(mflags))
        puts('[test]: repository build publish target in branch: {0}'.format(branch))
        puts('------------------------------------------------------------------------')

def main():
    with settings(hide('warnings'), warn_only=True):
        branches = get_branch_list()

    if branches == []:
        branches = ['master']

    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', '-b', default='master')
    parser.add_argument('--repo', '-r', default='git@github.com:mongodb/docs.git')
    user = parser.parse_args()

    bootstrap_test_env(user.repo)
    setup_docs_tools_repo()

    if user.branch == 'all':
        puts('[test]: testing build for each branch: {0}'.format(', '.join(branches)))
        for branch in branches:
            run_tests(branch)
    else:
        puts('[test]: running test build for branch {0}'.format(user.branch))
        run_tests(user.branch)

    puts('[test]: test sequence complete. examine output for errors.')

if __name__ == '__main__':
    main()
