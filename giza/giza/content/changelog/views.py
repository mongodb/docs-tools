# Copyright 2014 MongoDB, Inc.
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

import os
import logging
import collections

import giza.jeerah.client
import rstcloth.rstcloth as rstcloth

logger = logging.getLogger('giza.content.changelog.views')


def migrate_changelog(fn, conf):
    # because changelogs are generated in the source working dir we need to
    # migrate it into the build directory, and will use this as a finalizer.

    # filename relative to the top of the source directory
    base = fn[len(os.path.join(conf.paths.projectroot, conf.paths.source))+1:]
    target = os.path.join(conf.paths.projectroot, conf.paths.branch_source, base)

    giza.tools.files.copy_if_needed(fn, target, "changelog")


def get_issue_structure(version, conf):
    """
    Collect data from jira and produce a special headings structure for this version.
    """

    # set up and connect to jira
    jira = giza.jeerah.client.JeerahClient(conf)
    jira.connect()

    # run the jira query
    projects = ', '.join(conf.system.files.data.jira.site.projects)
    query = "project in ({0}) and fixVersion = {1} and resolution = 'Fixed' ORDER BY key ASC".format(projects, version)
    issues = jira.query(query)
    logger.info("building changelog for {0} with {1} issue(s)".format(version, len(issues)))

    # setup container of heading groups using the defined ordering.
    headings = collections.OrderedDict()
    for k in conf.system.files.data.jira.changelog.ordering:
        headings[k] = list()

    # invert the mapping of groups to components so we can filter
    groups = dict()
    for k, v in conf.system.files.data.jira.changelog.groups.items():
        for c in v:
            groups[c] = k

    # run through all issues, and put each one in the headings structure at the
    # best place
    for issue in issues:
        components = []
        for c in issue.fields.components:
            components.append(c.name)

            if c.name not in groups:
                logger.error("undefined component %s. update configuration before continuing", c.name)

        issue_pair = (issue.key.encode("utf-8"), issue.fields.summary.encode("utf-8"))

        if len(components) == 0:
            # if there isn't a component put this in the last grouping.
            headings[next(reversed(headings))].append(issue_pair)
        elif len(components) == 1:
            headings[groups[components[0]]].append(issue_pair)
        else:
            # if an issue has multiple components use the one that appears first
            # in the ordering of headings
            located = False
            for heading in groups:
                if heading in components:
                    headings[groups[heading]].append(issue_pair)
                    located = True
                    break

            # if we get here, we should stop the build because someone added a
            # ticket with a component and we don't know how to deal with this.
            if located is False:
                logger.error("skipping issue {0} in changelog {1} because its components aren't defined in the changelog configuration. Fix now.".format(issue_pair[0], version))
                raise SystemExit

    return headings


def get_changelog_content(fn, version, conf):
    """
    Builds and writes the heading based on the ordered mapping of heading groups
    to RST files in the source directory.
    """

    # this queries jira and builds an map[OrderedDict]list<issue_pairs>
    # structure that holds the data and groupings
    headings = get_issue_structure(version, conf)

    # invert the mapping of nested, so we can properly handle subheadings.
    nested = dict()
    for enclosing_level, sub_headings in conf.system.files.data.jira.changelog.nesting.items():
        for component in sub_headings:
            nested[component] = enclosing_level

    # build the changelog content itself.
    r = rstcloth.RstCloth()
    level = 3

    # headings and links
    r.ref_target("{0}-changelog".format(version))
    r.newline()
    r.heading(text="{0} Changelog".format(version), char=giza.content.helper.character_levels[level-1])
    r.newline()

    # process all of the issues by group.
    for heading, issues in headings.items():
        if heading in nested:
            # we deal with nested headings when we do their parent. skip here.
            continue
        else:
            if heading in conf.system.files.data.jira.changelog.nesting and len(issues) == 0:
                # if a heading has subheadings, and all are empty, then we should skip it entirely.
                empty_sub_headings = 0
                for sub in conf.system.files.data.jira.changelog.nesting[heading]:
                    if len(headings[sub]) == 0:
                        empty_sub_headings += 1
                if empty_sub_headings == len(conf.system.files.data.jira.changelog.nesting[heading]):
                    continue
            elif len(issues) == 0:
                # skip empty headings.
                continue

            # format the heading.
            r.heading(text=heading, indent=0,
                      char=giza.content.helper.character_levels[level])
            r.newline()

            if len(issues) == 1:
                r.content("{1} {0}".format(issues[0][1], r.role("issue", issues[0][0])), wrap=False)
            else:
                for issue in issues:
                    r.li("{1} {0}".format(issue[1], r.role("issue", issue[0])), wrap=False)
            r.newline()

            # repeat the above formatting with minor variations to do the nesting.
            if heading in conf.system.files.data.jira.changelog.nesting:
                for sub in conf.system.files.data.jira.changelog.nesting[heading]:
                    if len(headings[sub]) == 0:
                        continue

                    r.heading(text=sub, indent=0,
                              char=giza.content.helper.character_levels[level+1])
                    r.newline()

                    sub_issues = headings[sub]
                    if len(sub_issues) == 0:
                        r.content("{1} {0}".format(sub_issues[0][1].strip(), r.role("issue", sub_issues[0][0])), wrap=False)
                    else:
                        for issue in sub_issues:
                            r.li("{1} {0}".format(issue[1].strip(), r.role("issue", issue[0])), wrap=False)
                    r.newline()

    r.write(fn)
    logger.info("wrote changelog '{0}'. Commit this file independently.".format(fn))
    migrate_changelog(fn, conf)


def render_intermediate_files(fn, version, releases, conf):
    """
    Each major release series has an "intermediate" file that includes the
    changelog file for each release. This way, there's no requirement to change
    the changelog file every release.
    """

    r = rstcloth.RstCloth()
    for rel in releases:
        r.directive("include", "/includes/changelogs/releases/{0}.rst".format('.'.join([str(s) for s in rel])))
        r.newline()

    r.write(fn)
    migrate_changelog(fn, conf)
    logger.info("wrote intermediate versions file ")
