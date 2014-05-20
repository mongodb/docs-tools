import logging
import os.path

logger = logging.getLogger(os.path.basename(__file__))

from config.base import ConfigurationBase

class PathsConfig(ConfigurationBase):
    def __init__(self, obj, conf):
        super(PathsConfig, self).__init__(obj)
        self._conf = conf

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        logger.error("cannot set conf at this level")

    @property
    def output(self):
        return self.state['output']

    @output.setter
    def output(self, value):
        self.state['output'] = value

    @property
    def source(self):
        return self.state['source']

    @source.setter
    def source(self, value):
        self.state['source'] = value

    @property
    def includes(self):
        return self.state['includes']

    @includes.setter
    def includes(self, value):
        self.state['includes'] = value

    @property
    def images(self):
        return self.state['images']

    @images.setter
    def images(self, value):
        self.state['images'] = value

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = value

    @property
    def buildsystem(self):
        return self.state['buildsystem']

    @buildsystem.setter
    def buildsystem(self, value):
        self.state['buildsystem'] = value

    @property
    def builddata(self):
        return self.state['builddata']

    @builddata.setter
    def builddata(self, value):
        self.state['builddata'] = value

    @property
    def locale(self):
        return self.state['locale']

    @locale.setter
    def locale(self, value):
        self.state['locale'] = value

    @property
    def buildarchive(self):
        if 'buildarchive' not in self.state:
            self.buildarchive = None
        return os.path.join(self.output, 'archive')

    @buildarchive.setter
    def buildarchive(self, value):
        self.state['buildarchive'] = os.path.join(self.output, 'archive')

    @property
    def global_config(self):
        return os.path.join(self.buildsystem, 'data')

    @global_config.setter
    def global_config(self, value):
        logger.error('global_config is dynamically rendered')

    @property
    def projectroot(self):
        p = os.getcwd()
        self.state['projectroot'] = os.getcwd()
        return p

    @property
    def public(self):
        if 'public' not in self.state:
            self.public = None

        return self.state['public']

    @public.setter
    def public(self, value):
        if self.conf.runstate.language in (None, 'en'):
            public_path = 'public'
        else:
            public_path = '-'.join(('public', self.conf.runstate.language))

        self.state['public'] = os.path.join(self.output, public_path)

    @property
    def branch_output(self):
        if 'branch_output' not in self.state:
            self.branch_output = None

        return self.state['branch_output']

    @branch_output.setter
    def branch_output(self, value):
        self.state['branch_output'] = os.path.join(self.output, self.conf.git.branches.current)

    @property
    def branch_source(self):
        if 'branch_source' not in self.state:
            self.branch_source = None

        return self.state['branch_source']

    @branch_source.setter
    def branch_source(self, value):
        self.state['branch_source'] = os.path.join(self.branch_output, self.source)

    @property
    def branch_staging(self):
        if 'branch_staging' not in self.state:
            self.branch_staging = None

        return self.state['branch_staging']

    @branch_staging.setter
    def branch_staging(self, value):
        self.state['branch_staging'] = os.path.join(self.public, self.conf.git.branches.current)

    @property
    def global_config(self):
        if 'global_config' not in self.state:
            self.global_config = None

        return self.state['global_config']

    @global_config.setter
    def global_config(self, value):
        self.state['global_config'] = os.path.join(self.buildsystem, 'data')
