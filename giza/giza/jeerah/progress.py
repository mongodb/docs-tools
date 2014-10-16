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

import datetime

from giza.jeerah.query import equality, inequality

def query(j, app, conf):
    query_base = "project {0} and fixVersion {1} and status {2}"

    project = conf.site.projects
    sprint = conf.sprints.get_sprint_versions(conf.runstate.sprint)

    queries = [
        ('total', 'project {0} and fixVersion {1}'.format(equality(project), equality(sprint))),
        ('completed', query_base.format(equality(project), equality(sprint), equality(['Closed', 'Resolved']))),
        ('progressing', query_base.format(equality(project), equality(sprint), equality(['In Code Review', 'In Progress']))),
        ('remaining', query_base.format(equality(project), equality(sprint), equality(['Open', 'Reopened'])))
    ]

    ops = []

    for name, query in queries:
        ops.append(name)
        t = app.add('task')
        t.target = True
        t.job = j.query
        t.args = [query]
        t.description = "{0} Jira query".format(name)

    app.run()

    return dict(zip(ops, app.results))

def report(data, conf):
    sprint = conf.sprints.get_sprint(conf.runstate.sprint)

    result = {
        'breakdown': { },
        'counts': { },
        'meta': {
            'projects': conf.site.projects,
            'units': conf.reporting.units,
            'sprint': conf.sprints.get_sprint_versions(conf.runstate.sprint),
            'date': str(datetime.date.today()),
            'quota': sprint.quota,
        },
        'planning': {
            'burndown': { },
            'capacity': { },
        },
    }

    if 'staffing' in sprint:
        result['meta']['staffing'] = sprint.staffing

    for query, issues in data.items():
        result['breakdown'][query] = { }
        result['counts'][query] = 0

        for issue in issues:
            hours = issue.fields.customfield_10855

            if hours is None:
                hours = 0

            if issue.fields.assignee is None:
                assignee = 'Unassigned'
            else:
                assignee = issue.fields.assignee.name

            if assignee not in result['breakdown'][query]:
                result['breakdown'][query][assignee] = 0

            if conf.reporting.units == 'hours':
                result['breakdown'][query][assignee] += hours
            elif conf.reporting.units == 'days':
                result['breakdown'][query][assignee] += hours / 8
            elif conf.reporting.units == 'count':
                result['breakdown'][query][assignee] += 1

    for category in result['breakdown']:
        result['counts'][category] += sum(result['breakdown'][category].values())

    for person in result['breakdown']['completed']:
        if 'staffing' in sprint:
            if person in sprint.staffing:
                result['planning']['burndown'][person] = sprint.staffing[person] - result['breakdown']['completed'][person]

    for person in sprint.staffing:
        if person in result['breakdown']['total']:
            result['planning']['capacity'][person] = sprint.staffing[person] - result['breakdown']['total'][person]

    return result
