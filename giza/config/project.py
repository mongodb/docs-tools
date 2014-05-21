from config.base import RecursiveConfigurationBase

class ProjectConfig(RecursiveConfigurationBase):
    @property
    def name(self):
        return self.state['name']

    @name.setter
    def name(self, value):
        self.state['name'] = value

    @property
    def tag(self):
        return self.state['tag']

    @tag.setter
    def tag(self, value):
        self.state['tag'] = value

    @property
    def url(self):
        return self.state['url']

    @url.setter
    def url(self, value):
        self.state['url'] = value

    @property
    def title(self):
        return self.state['title']

    @title.setter
    def title(self, value):
        self.state['title'] = value

    @property
    def editions(self):
        return self.state['editions']

    @editions.setter
    def editions(self, value):
        if isinstance(value, list):
            self.state['editions'] = value
        else:
            logger.critical('editions must be a list')
            raise TypeError

    @property
    def edition(self):
        if 'edition' not in self.state or self.state['edition'] is None:
            self.edition = None
        return self.state['edition']

    @edition.setter
    def edition(self, value):
        if 'editions' in self.state and self.conf.runstate.edition in self.state['editions']:
            self.state['edition'] = self.conf.runstate.edition
        else:
            self.state['edition'] = None
