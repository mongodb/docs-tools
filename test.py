from fabric.api import local, hide, lcd, puts, settings, hide
import fabric.state
import os
import sys
import argparse

fabric.state.output.running = False

build = 'build'

def bootstrap_test_env(repo, repo_path):
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

def setup_docs_tools_repo(repo_path):
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

def get_branch_list(repo_path):
    with lcd(repo_path):
        branches = local('git branch -r --no-color --no-column', capture=True).stdout.split()
        branches = [ branch.split('/', 1)[1] for branch in set(branches) if len(branch.split('/', 1)) > 1 and not branch.split('/', 1)[1] == 'HEAD' ]
    return branches

def run_tests(branch, project, repo_path):
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
        
        if project == 'manual':
            pre_builders = 'json dirhtml texinfo'
            local('make {0} {1}'.format(mflags, pre_builders))
            puts('[test]: targets rebuilt: {0}.'.format(pre_builders))
            puts('------------------------------------------------------------------------')

        local('make {0} publish'.format(mflags))
        puts('[test]: repository build publish target in branch: {0}'.format(branch))
        puts('------------------------------------------------------------------------')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch', '-b', default='master')
    parser.add_argument('--repo', '-r', default='git@github.com:mongodb/docs.git')
    parser.add_argument('--project', '-p', default='manual', choices=['manual', 'mms', 'ecosystem'])
    user = parser.parse_args()

    if user.repo == 'git@github.com:mongodb/docs.git' and user.project != 'manual':
        exit('[test]: project and repo are not correctly matched')

    repo_path = os.path.join(build, user.project)
    bootstrap_test_env(user.repo, repo_path)
    setup_docs_tools_repo(repo_path)

    with settings(hide('warnings'), warn_only=True):
        branches = get_branch_list(repo_path)

    if branches == []:
        branches = ['master']

    if user.branch == 'all':
        puts('[test]: testing build for each branch: {0}'.format(', '.join(branches)))
        for branch in branches:
            run_tests(branch, user.project, repo_path)
    else:
        puts('[test]: running test build for branch {0}'.format(user.branch))
        run_tests(user.branch, user.project, repo_path)

    puts('[test]: test sequence complete. examine output for errors.')

if __name__ == '__main__':
    main()
