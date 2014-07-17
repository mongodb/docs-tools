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

from giza.jeerah.query import equality, inequality, query_link

def query(j, app, conf):
    ops = []
    query_strings = []

    timing_query_f = '"Actual Time" is EMPTY'
    fixversion_f = "fixversion is not EMPTY"
    uncategorized_f = "fixVersion is empty or component is empty"
    project = conf.site.projects
    buckets = conf.buckets.values()

    queries = [
        ('category', "project {0} and resolution = Unresolved and ({1})".format(equality(project), uncategorized_f)),
        ('timing', 'project {0} and fixVersion {1} and resolution = Unresolved and {2} and {3}'.format(equality(project), inequality(buckets), timing_query_f, fixversion_f)),
        ('combined', 'project {0} and resolution = Unresolved and (( {1} and {2} ) or ({3}))'.format(equality(project), timing_query_f, fixversion_f, uncategorized_f)),
    ]

    for name, query in queries:
        ops.append(name)
        query_strings.append(query)

        t = app.add('task')
        t.job = j.query
        t.args = [query]
        t.description = "{0} Jira query".format(name)

    app.run()

    return zip(ops, query_strings, app.results)

def report(data, conf):
    results = {
        'totals': {},
        'queries': {}
    }

    for name, query, issues in data:
        results['totals'][name] = len(issues)
        results['queries'][name] = query_link(conf.site.url, query)
        if len(issues) < 50:
            results[name] = [ '/'.join([conf.site.url, 'browse', i.key]) for i in issues ]
        else:
            results[name] = [ 'too many']

    return results
