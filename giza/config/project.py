from config.base import RecursiveConfigurationBase, ConfigurationBase

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
        if 'editions' in self.state:
            return self.state['editions']
        else:
            return []

    @editions.setter
    def editions(self, value):
        if isinstance(value, list):
            if '_edition_list' not in self.state:
                self.state['_edition_list'] = []

            self.state['_edition_list'].extend( [ v['name'] for v in value ] )
            self.state['editions'] = [EditionListConfig(v) for v in value]
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
        if 'editions' in self.state and self.conf.runstate.edition in self.state['_edition_list']:
            self.state['edition'] = self.conf.runstate.edition
        else:
            self.state['edition'] = self.name

    @property
    def branched(self):
        if 'branched' not in self.state:
            self.branched = None

        return self.state['branched']

    @branched.setter
    def branched(self, value):
        if isinstance(value, bool):
            self.state['branched'] = value
        else:
            self.state['branched'] = False
            for edition in self.editions:
                if self.edition == edition.name:
                    self.state['branched'] = edition.branched
                    break

    @property
    def basepath(self):
        if 'basepath' not in self.state:
            self.basepath = None

        return self.state['basepath']

    @basepath.setter
    def basepath(self, value):
        if value is not None:
            self.state['basepath'] = value
        else:
            self.state['basepath'] = self.tag

            for edition in self.editions:
                if self.edition == edition.name:
                    self.state['basepath'] = edition.tag
                    break


class EditionListConfig(ConfigurationBase):
    @property
    def name(self):
        return self.state['name']

    @name.setter
    def name(self, value):
        self.state['name'] = value

    @property
    def branched(self):
        if 'branched' in self.state:
            return self.state['branched']
        else:
            return False

    @branched.setter
    def branched(self, value):
        if isinstance(value, bool):
            self.state['branched'] = value
        else:
            raise TypeError

    @property
    def tag(self):
        if 'tag' not in self.state:
            return None
        else:
            return self.state['tag']

    @tag.setter
    def tag(self, value):
        self.state['tag'] = value
