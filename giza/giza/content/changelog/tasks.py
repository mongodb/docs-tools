# Copyright 2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
import logging

import giza.content.changelog.views
import giza.tools.files

from giza.config.content import new_content_type
from libgiza.task import Task

logger = logging.getLogger('giza.content.changelog.tasks')


def register_changelogs(conf):
    content_dfn = new_content_type(name='changelogs',
                                   task_generator=changelog_tasks,
                                   conf=conf)

    conf.system.content.add(name='changelogs', definition=content_dfn)


def get_major_version_groupings(versions):
    major_versions = {}
    for v in versions:
        parts = [int(i) for i in v.split(".")]
        mver = ".".join([str(s) for s in parts[0:2]])
        if mver not in major_versions:
            major_versions[mver] = [parts]
        else:
            major_versions[mver].append(parts)

    for v in major_versions.values():
        v.sort(reverse=True)

    return major_versions


def changelog_tasks(conf):
    tasks = []

    if "jira" not in conf.system.files.data:
        logger.warning("changelog generation is not configured.")
        return []

    dirname = os.path.join(conf.paths.projectroot, conf.paths.includes, "changelogs")

    giza.tools.files.safe_create_directory(os.path.join(dirname, "releases"))
    jira_config = os.path.join(conf.paths.projectroot, conf.paths.builddata, "jira.yaml")
    major_versions = get_major_version_groupings(conf.system.files.data.jira.site.versions)

    # If no version listed in jira.yaml, just return; Should be same
    # as if jira is not configured  in conf.system.files.data
    # Also, log explicit message stating that 0 changelog tasks added.
    if not major_versions:
        logger.warning("changelog version is not configured in jira.yaml.")
        logger.info("added {0} changelog tasks.".format(len(tasks)))
        return []

    # don't generate changelog content except on the most recent published
    # branch (i.e. master, typically.).
    if conf.git.branches.current != conf.git.branches.published[0]:
        logger.error("you must generate changelogs on the master branch and them backport them to another branch.")
        logger.info("added {0} changelog tasks".format(len(tasks)))
        return tasks

    # only generate changelogs if there are credentials, even though we don't
    # really need an auth'ed connection, want to avoid making un-authed builds too long.
    if not os.path.exists(os.path.expanduser(conf.system.files.data.jira.site.credentials)):
        logger.warning("jira credentials are not configured for your user. not generating changelog tasks")
        logger.info("added {0} changelog tasks".format(len(tasks)))
        return tasks

    # bump mtime of all existing files to avoid regenerating files that already committed files
    # exist.
    changelog_releases_dir = os.path.join(conf.paths.projectroot, conf.paths.includes, "changelogs", "releases")

    for fn in os.listdir(changelog_releases_dir):
        os.utime(os.path.join(changelog_releases_dir, fn), None)

    # add tasks for generating intermediate files for each major version. we do
    # this on all branches, and publishers need to backport the config changes.
    for version, releases in major_versions.items():
        fn = os.path.join(dirname, version + ".rst")
        t = Task(job=giza.content.changelog.views.render_intermediate_files,
                 args=(fn, version, releases, conf),
                 target=fn,
                 dependency=[jira_config])
        tasks.append(t)

    # create a task for each version defined. should never regenerate existing files.
    for version in  conf.system.files.data.jira.site.versions:
        fn = os.path.join(conf.paths.projectroot, conf.paths.includes, "changelogs", "releases", version + ".rst")
        t = Task(job=giza.content.changelog.views.get_changelog_content,
                 args=(fn, version, conf),
                 dependency=[jira_config],
                 target=fn)
        tasks.append(t)

    logger.info("added {0} changelog tasks.".format(len(tasks)))
    return tasks
