#!/usr/bin/env python3
import fnmatch
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import List

PAT_URL = re.compile('.+/(.+).git')


def git_get_commit_hash(branch: str, build_dir: str) -> str:
    return str(subprocess.check_output(['git', 'rev-parse', 'master'], cwd=build_dir), 'utf-8').strip()


class BuildTask:
    def __init__(self, build_dir: str, build_command: str) -> None:
        self.build_dir = build_dir
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

        subprocess.check_call(self.build_command, shell=True, cwd=self.build_dir)


def clone(url: str, branch: str, dest: str) -> None:
    subprocess.check_call(['git', 'clone', url, dest])
    subprocess.check_call(['git', 'checkout', branch], cwd=dest)


def pull(path: str, branch: str) -> None:
    subprocess.check_call(['git', 'fetch', '-q'], cwd=path)
    subprocess.check_call(['git', 'reset', '-q', '--hard'], cwd=path)
    subprocess.check_call(['git', 'checkout', '-q', branch], cwd=path)


def build(project, patterns) -> List[BuildTask]:
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
            clone(project['git'], branch, output_dir)
        else:
            pull(output_dir, branch)

        if project.get('docs-tools', False):
            try:
                os.mkdir(os.path.join(output_dir, 'build'))
            except FileExistsError:
                pass

            try:
                os.symlink('../../docs-tools', os.path.join(output_dir, 'build', 'docs-tools'))
            except FileExistsError:
                pass

        build_tasks.append(BuildTask(output_dir, project['build']))

    return build_tasks


def main(path: str, patterns_text: List[str]):
    with open(path, 'r') as f:
        data = json.load(f)

    patterns = [re.compile(fnmatch.translate(text)) for text in patterns_text]

    # Pull docs-tools
    if not os.path.isdir('build/docs-tools'):
        clone('https://github.com/mongodb/docs-tools.git', 'master', 'build/docs-tools')
    else:
        pull('build/docs-tools', 'master')

    tasks = []
    for project in data:
        tasks.extend(build(project, patterns))

    for task in tasks:
        try:
            task.build()
        except subprocess.SubprocessError:
            print('Failed to build!')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        patterns = sys.argv[1:]
    else:
        patterns = ['*']

    main('projects.json', patterns)
