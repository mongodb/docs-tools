from giza.config.base import RecursiveConfigurationBase

class VersionConfig(RecursiveConfigurationBase):
    @property
    def release(self):
        return self.state['release']

    @release.setter
    def release(self, value):
        self.state['release'] = value

    @property
    def branch(self):
        return self.state['branch']

    @branch.setter
    def branch(self, value):
        self.state['branch'] = value

    @property
    def published(self):
        if 'published' not in self.state:
            self.published = None

        return self.state['published']

    @published.setter
    def published(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'published' in self.conf.runstate.branch_conf['version']:
            p = self.conf.runstate.branch_conf['version']['published']

            if not isinstance(p, list):
                msg = "published branches must be a list"
                logger.critical(msg)
                raise TypeError(msg)

            self.state['published'] = p
        else:
            self.state['published'] = []

    @property
    def upcoming(self):
        if 'upcoming' not in self.state:
            self.upcoming = None

        return self.state['upcoming']

    @upcoming.setter
    def upcoming(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'upcoming' in self.conf.runstate.branch_conf['version']:
            self.state['upcoming'] = self.conf.runstate.branch_conf['version']['upcoming']
        else:
            self.state['upcoming'] = None

    @property
    def stable(self):
        if 'stable' not in self.state:
            self.stable = None

        return self.state['stable']

    @stable.setter
    def stable(self, value):
        if 'version' in self.conf.runstate.branch_conf and 'stable' in self.conf.runstate.branch_conf['version']:
            self.state['stable'] = self.conf.runstate.branch_conf['version']['stable']
        else:
            self.state['stable'] = None
