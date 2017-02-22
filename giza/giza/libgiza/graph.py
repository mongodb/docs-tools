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

import copy


def get_dependency_graph(app):
    graph = {}

    tasks = copy.copy(app.queue)
    for task in tasks:
        if isinstance(task.target, list):
            for target in task.target:
                if target not in graph:
                    graph[target] = []
                if isinstance(task.dependency, list):
                    graph[target].extend(task.dependency)
                else:
                    graph[target].append(task.dependency)
            continue
        elif task.target not in graph:
            graph[task.target] = []

        if task.target is None:
            print(type(task),
                  task.dependency if hasattr(task, 'dependency') else "no dep",
                  task.job if hasattr(task, 'job') else "no job",
                  task.description if hasattr(task, 'description') else "no text")

        if isinstance(task.dependency, list):
            graph[task.target].extend(task.dependency)
        else:
            graph[task.target].append(task.dependency)

    return graph
