#!/usr/bin/env python3
import fnmatch
import json
import os
import re
import subprocess
import sys
from typing import List, Optional

PAT_URL = re.compile('.+/(.+).git')


class BuildTask:
    def __init__(self, branch: str, build_dir: str, build_redirects_command: Optional[str], build_command: str) -> None:
        self.branch = branch
        self.build_dir = build_dir
        self.build_redirects_command = build_redirects_command
        self.build_command = build_command
        self.built_flag_file = os.path.join(self.build_dir, '.built')

    def build(self) -> None:
        print('Building ' + self.build_dir)
        subprocess.check_call(['git', 'clean', '-xfd'], cwd=self.build_dir)

        # Some of our properties die if these directories do not exist
        for path in ('build', 'build/master', 'build/public', 'build/public/master'):
            try:
                os.mkdir(os.path.join(self.build_dir, path))
            except OSError:
                pass

        if self.build_redirects_command is not None:
            checkout(self.build_dir, 'master')
            subprocess.check_call(self.build_redirects_command, shell=True, cwd=self.build_dir)

        checkout(self.build_dir, self.branch)
        subprocess.check_call(self.build_command, shell=True, cwd=self.build_dir)


def clone(url: str, dest: str) -> None:
    subprocess.check_call(['git', 'clone', url, dest])


def fetch(path: str) -> None:
    subprocess.check_call(['git', 'fetch', '-q'], cwd=path)


def checkout(path: str, branch: str) -> None:
    subprocess.check_call(['git', 'checkout', '-q', branch], cwd=path)
    subprocess.check_call(['git', 'reset', '--hard', 'origin/{}'.format(branch)], cwd=path)


def build(project, patterns) -> List[BuildTask]:
    project_name = project.get('name', None)
    if not project_name:
        project_name = PAT_URL.match(project['git']).group(1)

    try:
        os.mkdir('build')
    except OSError:
        pass

    build_tasks = []
    for branch in project['branches']:
        full_branch_name = '-'.join((project_name, branch))
        matched = False
        for pattern in patterns:
            if pattern.match(full_branch_name):
                matched = True
                break

        if not matched:
            continue

        output_dir = os.path.join('build', full_branch_name)
        if not os.path.isdir(output_dir):
            clone(project['git'], output_dir)
        else:
            fetch(output_dir)

        if project.get('docs-tools', True):
            try:
                os.mkdir(os.path.join(output_dir, 'build'))
            except FileExistsError:
                pass

            try:
                os.symlink('../../docs-tools', os.path.join(output_dir, 'build', 'docs-tools'))
            except FileExistsError:
                pass

        build_tasks.append(
            BuildTask(
                branch,
                output_dir,
                project.get(
                    'build_redirects',
                    "mut-redirects config/redirects -o build/public/.htaccess"),
                project['build']))

    return build_tasks


def main(path: str, patterns_text: List[str]):
    with open(path, 'r') as f:
        data = json.load(f)

    patterns = [re.compile(fnmatch.translate(text)) for text in patterns_text]

    # Pull docs-tools
    if not os.path.isdir('build/docs-tools'):
        clone('https://github.com/mongodb/docs-tools.git', 'build/docs-tools')
    else:
        fetch('build/docs-tools')

    checkout('build/docs-tools', 'master')

    tasks = []
    for project in data:
        tasks.extend(build(project, patterns))


    errors = []  # type: List[str]
    for task in tasks:
        try:
            task.build()
        except subprocess.SubprocessError:
            errors.append(task.build_dir)
            print('Failed to build in {}'.format(task.build_dir))

    if errors:
        print('\nFailed to build:')
        for d in errors:
            print('  ' + d)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        patterns = sys.argv[1:]
    else:
        patterns = ['*']

    main('projects.json', patterns)
