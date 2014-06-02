from giza.config.base import ConfigurationBase

class DeployConfig(ConfigurationBase):
    @property
    def production(self):
        return self.state['production']

    @production.setter
    def production(self, value):
        self.state['production'] = DeployTargetConfig(value)

    @property
    def staging(self):
        return self.state['staging']

    @staging.setter
    def staging(self, value):
        self.state['staging'] = DeployTargetConfig(value)

    @property
    def testing(self):
        return self.state['testing']

    @staging.setter
    def testing(self, value):
        self.state['testing'] = DeployTargetConfig(value)

class DeployTargetConfig(ConfigurationBase):
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
