import logging
import os.path

import yaml

logger = logging.getLogger(os.path.basename(__file__))

from utils.structures import BuildConfiguration, AttributeDict
from utils.serialization import ingest_yaml_doc
from utils.shell import CommandError

class ConfigurationBase(object):
    def __init__(self, input_obj=None):
        self._state = {}
        self.ingest(input_obj)

    def ingest(self, input_obj=None):
        if input_obj is None:
            return
        elif isinstance(input_obj, dict):
            pass
        elif os.path.exists(input_obj):
            input_obj = ingest_yaml_doc(input_obj)
        else:
            msg = 'cannot ingest Configuration obj from object with type {0}'.format(type(input_obj).name)
            logger.critical(msg)
            raise TypeError(msg)

        for key, value in input_obj.items():
            setattr(self, key, value)
            logger.debug('setting {0} using default setter in {1} object'.format(key, type(self)))

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        logger.warning('cannot set state record directly')

    def __contains__(self, key):
        return key in self.state

    def __setattr__(self, key, value):
        if key.startswith('_') or key in dir(self):
            object.__setattr__(self, key, value)
        else:
            msg = 'configuration object {0} lacks support for "{1}" value'.format(type(self), key)
            logger.critical(msg)
            # raise TypeError(msg)

    @staticmethod
    def _is_value_type(value):
        acceptable_types = (ConfigurationBase, basestring, list, int, long,
                            float, complex)

        if isinstance(value, acceptable_types):
            return True
        else:
            return False

    def __repr__(self):
        return str(self.state)

    def dict(self):
        d = {}
        for k,v in self.state.items():
            if isinstance(v, ConfigurationBase):
                d[k] = v.dict()
            else:
                d[k] = v
        return d

class RecursiveConfigurationBase(ConfigurationBase):
    def __init__(self, obj, conf):
        super(RecursiveConfigurationBase, self).__init__(obj)
        self._conf = None
        self.conf = conf

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, Configuration):
            self._conf = value
        else:
            m = 'invalid configuration object: {0}'.format(value)
            m.error(m)
            raise TypeError(m)


class ProjectConfig(ConfigurationBase):
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

from utils.git import GitRepo

class GitConfigBase(ConfigurationBase):
    def __init__(self, obj, conf, repo=None):
        super(GitConfigBase, self).__init__(obj)
        self._conf = conf
        self._repo = repo

    @property
    def repo(self):
        return self._repo

    @repo.setter
    def repo(self, path=None):
        if self._repo is None:
            self._repo = GitRepo(path)

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        logger.error("cannot set conf at this level")

class GitConfig(GitConfigBase):
    @property
    def commit(self):
        c = self.repo.sha('HEAD')
        self.state['commit'] = c
        return c

    @property
    def branches(self):
        if 'branches' not in self.state:
            self.branches = None
        return self.state['branches']

    @branches.setter
    def branches(self, value):
        self.state['branches'] = GitBranchConfig(None, self.conf, self.repo)

    @property
    def remote(self):
        if 'remote' not in self.state:
            self.remote = None
        return self.state['remote']

    @remote.setter
    def remote(self, value):
        self.state['remote'] = GitRemoteConfig(value)


class GitRemoteConfig(ConfigurationBase):
    @property
    def upstream(self):
        return self.state['upstream']

    @upstream.setter
    def upstream(self, value):
        self.state['upstream'] = value

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = value

class GitBranchConfig(GitConfigBase):
    @property
    def current(self):
        if 'current' not in self.state:
            self.current = None

        return self.state['current']

    @current.setter
    def current(self, value):
        self.state['current'] = self.repo.current_branch()

    @property
    def manual(self):
        if 'manual' not in self.state:
            self.manual = None

        return self.state['manual']

    @manual.setter
    def manual(self, value):
        if 'manual' in self.conf.runstate.branch_conf['git']['branches']:
            self.state['manual'] = self.conf.runstate.branch_conf['git']['branches']['manual']
        else:
            self.state['manual'] = None

    @property
    def published(self):
        if 'published' not in self.state:
            self.published = None

        return self.state['published']

    @published.setter
    def published(self, value):
        if 'published' in self.conf.runstate.branch_conf['git']['branches']:
            p = self.conf.runstate.branch_conf['git']['branches']['published']

            if not isinstance(p, list):
                msg = "published branches must be a list"
                logger.critical(msg)
                raise TypeError(msg)

            self.state['published'] = p
        else:
            self.state['published'] = []

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

class Configuration(ConfigurationBase):
    @property
    def project(self):
        return self.state['project']

    @project.setter
    def project(self, value):
        self.state['project'] = ProjectConfig(value)

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
        if isinstance(value, RuntimeStateConfiguration):
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
        self.state['version'] = VersionConfiguration(value, self)

    @property
    def system(self):
        if 'system' not in self.state:
            self.system = None

        return self.state['system']

    @system.setter
    def system(self, value):
        self.state['system'] = SystemConfiguration(value)

    @property
    def assets(self):
        return self.state['assets']

    @assets.setter
    def assets(self, value):
        if isinstance(value, list):
            self.state['assets'] = value
        else:
            self.state['assets'] = [value]

class SystemConfiguration(ConfigurationBase):
    @property
    def make(self):
        return self.state['make']

    @make.setter
    def make(self, value):
        self.state['make'] = SystemMakeConfiguration(value)

    @property
    def tools(self):
        return self.state['tools']

    @tools.setter
    def tools(self, value):
        self.state['tools'] = value

class SystemToolsConfiguration(ConfigurationBase):
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

class SystemMakeConfiguration(ConfigurationBase):
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

class VersionConfiguration(RecursiveConfigurationBase):
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
        if 'published' in self.conf.runstate.branch_conf['version']:
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
        if 'upcoming' in self.conf.runstate.branch_conf['version']:
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
        if 'stable' in self.conf.runstate.branch_conf['version']:
            self.state['stable'] = self.conf.runstate.branch_conf['version']['stable']
        else:
            self.state['stable'] = None

class RuntimeStateConfiguration(ConfigurationBase):
    def __init__(self, obj=None):
        super(RuntimeStateConfiguration, self).__init__(obj)
        self._branch_conf = None
        self._conf = None

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, value):
        if isinstance(value, Configuration):
            self._conf = value
        else:
            m = 'invalid configuration object: {0}'.format(value)
            m.error(m)
            raise TypeError(m)

    @property
    def language(self):
        if 'language' not in self.state:
            return 'en'
        else:
            return self.state['language']

    @language.setter
    def language(self, value):
        self.state['language'] = value

    @property
    def branch_conf(self):
        if self._branch_conf is None:
            self.branch_conf = None

        return self._branch_conf

    @branch_conf.setter
    def branch_conf(self, value):
        fn = os.path.join(self.conf.paths.builddata, 'published_branches.yaml')

        if self.conf.git.branches.current == 'master'and not os.path.exists(fn):
            self._branch_conf = {}
        else:
            try:
                data = self.conf.git.repo.branch_file(path=fn, branch='master')
            except CommandError:
                logger.critical('giza not configured to work with buildbot repos')
                self._branch_conf = {}
                return

            self._branch_conf = yaml.load(data)
