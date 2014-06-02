from giza.config.base import ConfigurationBase

class AssetsConfig(ConfigurationBase):
    @property
    def path(self):
        self.state['path']

    @path.setter
    def path(self, value):
        self.state['path'] = value

    @property
    def branch(self):
        self.state['branch']

    @branch.setter
    def branch(self, value):
        self.state['branch'] = value

    @property
    def repository(self):
        self.state['repository']

    @repository.setter
    def repository(self, value):
        self.state['repository'] = value
