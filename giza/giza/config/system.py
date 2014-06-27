import logging
import os.path

logger = logging.getLogger('giza.config.system')

from giza.config.base import RecursiveConfigurationBase, ConfigurationBase

class SystemConfig(RecursiveConfigurationBase):
    @property
    def make(self):
        return self.state['make']

    @make.setter
    def make(self, value):
        self.state['make'] = SystemMakeConfig(value)

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = SystemToolsConfig(value)

    @property
    def conf_file(self):
        if 'conf_file' not in self.state:
            self.conf_file = None

        return self.state['conf_file']

    @conf_file.setter
    def conf_file(self, value):
        pass

    @property
    def branched(self):
        return self.conf.project.branched

    @branched.setter
    def branched(self, value):
        logger.warning('branched state is stored in system not project.')

    @property
    def dependency_cache(self):
        if 'dependency_cache' not in self.state:
            self.dependency_cache = None

        return self.state['dependency_cache']

    @dependency_cache.setter
    def dependency_cache(self, value):
        if value is not None:
            self.state['dependency_cache'] = value
        else:
            p = [ self.conf.paths.projectroot, self.conf.paths.branch_output ]
            if self.conf.project.edition is None:
                p.append('dependencies.json')
            else:
                p.append('dependencies-' + self.conf.project.edition + '.json')

            self.state['dependency_cache'] = os.path.sep.join(p)

class SystemToolsConfig(ConfigurationBase):
    @property
    def pinned(self):
        return self.state['pinned']

    @pinned.setter
    def pinned(self, value):
        if isinstance(value, bool):
            self.state['pinned'] = value
        else:
            raise TypeError

    @property
    def ref(self):
        return self.state['ref']

    @ref.setter
    def ref(self, value):
        if value in ('HEAD', 'master') or len(value) == 40:
            self.state['ref'] = value
        else:
            raise TypeError

class SystemMakeConfig(ConfigurationBase):
    @property
    def generated(self):
        return self.state['generated']

    @generated.setter
    def generated(self, value):
        if isinstance(value, list):
            self.state['generated'] = value
        else:
            raise TypeError

    @property
    def static(self):
        return self.state['static']

    @static.setter
    def static(self, value):
        if isinstance(value, list):
            self.state['static'] = value
        else:
            raise TypeError
