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
import giza.jeerah.progress

def report(data, conf):
    sprint = conf.sprints.get_sprint(conf.runstate.sprint)

    result = {
        'burndown': { },
        'capacity': { },
        'meta': {
            'projects': conf.site.projects,
            'units': conf.reporting.units,
            'sprint': conf.sprints.get_sprint_versions(conf.runstate.sprint),
            'date': str(datetime.date.today()),
            'quota': sprint.quota,
            'overage': 0,
        }
    }

    query_data = giza.jeerah.progress.process_query(data, conf)

    if 'staffing' in sprint:
        result['staffing'] = sprint.staffing

    for person in query_data['completed']:
        if 'staffing' in sprint:
            if person in sprint.staffing:
                result['burndown'][person] = sprint.staffing[person] - query_data['completed'][person]

    for person in sprint.staffing:
        if person in query_data['total']:
            result['capacity'][person] = sprint.staffing[person] - query_data['total'][person]

    for overage in result['capacity'].values():
        if overage < 0:
            result['meta']['overage'] += -1 * overage

    return result
