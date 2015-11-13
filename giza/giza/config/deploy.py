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

import re
import logging
import libgiza.config

logger = logging.getLogger('giza.config.deploy')


class DeployConfig(libgiza.config.ConfigurationBase):
    @property
    def production(self):
        return self.state['production']

    @production.setter
    def production(self, value):
        self.state['production'] = DeployTargetConfig(value)

    @property
    def testing(self):
        return self.state['testing']

    @testing.setter
    def testing(self, value):
        self.state['testing'] = DeployTargetConfig(value)

    @property
    def docsprod(self):
        return self.state['docsprod']

    @docsprod.setter
    def docsprod(self, value):
        self.state['docsprod'] = DeployTargetConfig(value)

    def get_staging(self, project):
        """Returns the appropriate StagingTargetConfig staging configuration for
           the current project."""
        try:
            return self.state['staging'][project]
        except KeyError as err:
            logger.critical('No staging information specified for project %s',
                            project)
            raise err

    def get_deploy(self, project):
        """Returns the appropriate StagingTargetConfig deployment configuration
           for the current project."""
        try:
            return self.state['s3_deploy'][project]
        except KeyError as err:
            logger.critical('No deployment information specified for project %s',
                            project)
            raise err

    @property
    def staging(self):
        return self.state['staging']

    @staging.setter
    def staging(self, value):
        self.state['staging'] = {}
        for project, config in value.items():
            self.state['staging'][project] = StagingTargetConfig(config)

    @property
    def s3_deploy(self):
        return self.state['s3_deploy']

    @s3_deploy.setter
    def s3_deploy(self, value):
        self.state['s3_deploy'] = {}
        for project, config in value.items():
            self.state['s3_deploy'][project] = StagingTargetConfig(config)


class DeployTargetConfig(libgiza.config.ConfigurationBase):
    _option_registry = ['input']

    @property
    def args(self):
        return self.state['args']

    @args.setter
    def args(self, value):
        if isinstance(value, list):
            self.state['args'] = value
        else:
            logger.critical('deployment arguments must be a list')
            raise TypeError

    @property
    def hosts(self):
        return self.state['hosts']

    @hosts.setter
    def hosts(self, value):
        if isinstance(value, list):
            self.state['hosts'] = value
        else:
            logger.critical('deployment targets must be a list')
            raise TypeError


class StagingTargetConfig(libgiza.config.ConfigurationBase):
    """Configuration for a project's staging environment, specifying both an S3
       bucket and an HTTP/S URL pointing to that bucket, appropriate for user
       consumption."""
    @property
    def url(self):
        try:
            return self.state['url']
        except KeyError as err:
            logger.critical('No staging URL specified')
            raise err

    @url.setter
    def url(self, value):
        self.state['url'] = str(value)

    @property
    def bucket(self):
        try:
            return self.state['bucket']
        except KeyError as err:
            logger.critical('No staging bucket specified')
            raise err

    @bucket.setter
    def bucket(self, value):
        self.state['bucket'] = str(value)

    @property
    def prefix(self):
        """The prefix underwhich giza will upload everything in the bucket."""
        try:
            return self.state['prefix']
        except KeyError as err:
            return ''

    @prefix.setter
    def prefix(self, value):
        self.state['prefix'] = str(value)

    @property
    def use_branch(self):
        """Specifies whether only the directory corresponding to the current
           git branch should be uploaded. False if giza should upload
           everything."""
        try:
            return self.state['use_branch']
        except KeyError as err:
            return True

    @use_branch.setter
    def use_branch(self, value):
        self.state['use_branch'] = bool(value)

    @property
    def redirect_dirs(self):
        """A list of directory regular expressions for which this project
           is considered to "own" redirects. Redirects outside of these
           directories will never be removed (but may be modified) by
           this project."""
        try:
            return self.state['redirect_dirs']
        except KeyError as err:
            return []

    @redirect_dirs.setter
    def redirect_dirs(self, value):
        self.state['redirect_dirs'] = [re.compile(d) for d in value]
