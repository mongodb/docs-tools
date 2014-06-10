from giza.config.base import ConfigurationBase

class AssetsConfig(ConfigurationBase):
    @property
    def path(self):
        return self.state['path']

    @path.setter
    def path(self, value):
        self.state['path'] = value

    @property
    def branch(self):
        return self.state['branch']

    @branch.setter
    def branch(self, value):
        self.state['branch'] = value

    @property
    def repository(self):
        return self.state['repository']

    @repository.setter
    def repository(self, value):
        self.state['repository'] = value
