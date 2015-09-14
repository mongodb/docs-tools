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

"""
The complete goal for this component is to take the results of a Jira query and
generate RST with the contents of that change log at release so that we can
remove several manual steps from the larger release project.

Requirements/Features:

1. For every minor release, the system will create a single file that the
   publication/push manager will need to review, edit, and commit.

   - The /release-notes/<release-series>-changelog.txt file can be generated
     from template if it doesn't exist.

   - There will be an intermediate generated file that we will be ignored from
     git regenerated on as needed? and will include all of the generated files
     with each version so that.

   - The system will do auto-backfill for all of the covered versions *if* the
     files don't exist.

2. Configuration for the properties (i.e. components, projects, JIRA instances,)
   should be in the global (ie. docs-tools/data) directory. Configuration for
   actual generation (file locations, paths, etc.) should pull from the
   site configuration object and other config should be a linked configuration
   file.

3. Builds of the documentation should *not* (re)generate change-logs for new
   entries, nor should they expect that JIRA be available or responsive.

Implementation Steps:

- Model new configuration data.
- Generate new pages:
  - change log master page
  - intermediate include file
  - minor release change log.
- Create severable tasks.
- Add entry points.
- Convert existing data on the 2.6 and 3.0 (master) branches of the documentation.
"""
