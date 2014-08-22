# 2014 MongoDB, Inc.
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

def edition_check(data, conf):
    """
    Tests a content structure against the current configuration object to ensure
    that the editions match. Used so that content generation scripts can
    consistently filter out content from non-matching editions.

    :param dict,object data: A dictionary or object that holds content.

    :param giza.config.main.Configuration conf: A Configuration object. 

    :returns: ``True`` if ``data`` does not contain an ``edition`` field or
       attribute of ``data`` matches the value of
       ``conf.project.edition``. ``False`` if the edition does not match
       ``conf.project.edition`` or if ``conf.project.edition`` is the same as
       the project name (i.e. ``conf.project.name``).

    :rtype: Boolean
    """

    if 'edition' in data:
        try:
            local_edition = data.edition
        except AttributeError:
            local_edition = data['edition']

        if conf.project.edition != conf.project.name and local_edition != conf.project.edition:
            return False
        else: 
            return True
    else:
        return True
