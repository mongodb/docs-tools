#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import yaml
from typing import Any, Dict, Optional, Set, List

PAT_URL = re.compile('.+/(.+).git')


class BuildTask:
    def __init__(self, name: str, branches: List[str], build_dir: str, build_command: str) -> None:
        self.name = name
        self.branches = branches
        self.build_dir = build_dir
        self.build_command = build_command
        self.built_flag_file = os.path.join(self.build_dir, '.built')

    def build(self) -> None:
        subprocess.check_call(['git', 'clean', '-xfd'], cwd=self.build_dir)
        # Some of our properties die if these directories do not exist
        for path in ('build', 'build/master', 'build/public', 'build/public/master'):
            try:
                os.mkdir(os.path.join(self.build_dir, path))
            except OSError:
                pass

        for branch in self.branches:
            print('Building ' + self.build_dir)
            subprocess.check_call(['git', 'checkout', '-q', branch], cwd=self.build_dir)
            subprocess.check_call(['git', 'pull', '--ff-only', '-q'], cwd=self.build_dir)
            subprocess.check_call(self.build_command, shell=True, cwd=self.build_dir)


def load_branches_from_yaml(path: str) -> List[str]:
    with open(path, 'r') as f:
        loaded = yaml.safe_load(f)

    return loaded['git']['branches']['published']


def initialize_project(project: Dict[str, Any]) -> BuildTask:
    git_url = project['git']
    project_name = project.get('name', None)
    if not project_name:
        match = PAT_URL.match(git_url)
        if not match:
            raise ValueError('Cannot determine project name: {}'.format(git_url))
        project_name = match.group(1)

    branches = project['branches']
    if isinstance(branches, str):
        branches = load_branches_from_yaml(branches)

    output_dir = os.path.join('build', project_name)
    if not os.path.isdir(output_dir):
        print('Cloning {}'.format(git_url))
        subprocess.check_call(['git', 'clone', '-q', git_url, output_dir])

    return BuildTask(
            project_name,
            branches,
            output_dir,
            project['build'])


def main(path: str, projects: Optional[Set[str]]) -> None:
    with open(path, 'r') as f:
        data = json.load(f)

    tasks = []
    for project in data:
        task = initialize_project(project)
        if projects is None or task.name in projects:
            tasks.append(task)

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
        projects = set(sys.argv[1:])  # type: Optional[Set[str]]
    else:
        projects = None

    main('projects.json', projects)
