import os.path

from giza.tools.serialization import ingest_yaml_doc

from giza.config.base import ConfigurationBase, RecursiveConfigurationBase
from giza.config.assets import AssetsConfig
from giza.config.project import ProjectConfig
from giza.config.paths import PathsConfig
from giza.config.git import GitConfig
from giza.config.system import SystemConfig
from giza.config.runtime import RuntimeStateConfig
from giza.config.version import VersionConfig
from giza.config.deploy import DeployConfig

class Configuration(ConfigurationBase):
    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = ProjectConfig(value, self)

    @property
    def paths(self):
        return self.state['paths']

    @paths.setter
    def paths(self, value):

        self.state['paths'] = PathsConfig(value, self)

    @property
    def git(self):
        if 'git' not in self.state:
            self.git = None

        return self.state['git']

    @git.setter
    def git(self, value):
        c = GitConfig(value, self)
        c.repo = self.paths.projectroot
        self.state['git'] = c

    @property
    def runstate(self):
        return self.state['runstate']

    @runstate.setter
    def runstate(self, value):
        if isinstance(value, RuntimeStateConfig):
            value.conf = self
            self.state['runstate'] = value
        else:
            msg = "invalid runtime state"
            logger.critical(msg)
            raise TypeError(msg)

    @property
    def version(self):
        if 'version' not in self.state:
            self.version = None

        return self.state['version']

    @version.setter
    def version(self, value):
        self.state['version'] = VersionConfig(value, self)

    @property
    def system(self):
        if 'system' not in self.state:
            self.system = None

        return self.state['system']

    @system.setter
    def system(self, value):
        self.state['system'] = SystemConfig(value, self)

    @property
    def assets(self):
        return self.state['assets']

    @assets.setter
    def assets(self, value):
        if isinstance(value, list):
            self.state['assets'] = [AssetsConfig(v) for v in value]
        else:
            self.state['assets'] = [AssetsConfig(value)]

    @property
    def deploy(self):
        if 'deploy' not in self.state:
            self.deploy = None
        return self.state['deploy']

    @deploy.setter
    def deploy(self, value):
        fn = os.path.join(self.paths.global_config, 'deploy.yaml')
        if os.path.exists(fn):
            self.state['deploy'] = DeployConfig(fn)
        else:
            self.state['deploy'] = {}
