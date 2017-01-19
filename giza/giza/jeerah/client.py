import logging
import datetime

from jira.client import JIRA
from jira.resources import Version

import giza.config.credentials

logger = logging.getLogger('giza.jeerah.client')


class JeerahClient(object):
    def __init__(self, conf):
        self.conf = conf
        self.credentials = giza.config.credentials.CredentialsConfig(self.conf.system.files.data.jira.site.credentials).jira
        self.c = None
        self.issues_created = []
        self.abort_on_error = True
        self._results_format = 'list'
        self.versions_cache = {}

    @property
    def results_format(self):
        return self._results_format

    @results_format.setter
    def results_format(self, value):
        if value not in ("list", "dict"):
            m = "{0} is not in '{1}'", "value", ', '.join("list", "dict")
            logger.error(m)
            raise TypeError(m)
        else:
            self._results_format = value

    def connect(self):
        if self.c is None:
            self.c = JIRA(options={'server': self.credentials.url},
                          basic_auth=(self.credentials.username,
                                      self.credentials.password))
            logger.debug('created jira connection')
        else:
            logger.debug('jira connection exists')

        logger.debug('configured user: ' + self.credentials.username)
        logger.debug('actual user: ' + self.c.current_user())

    def connect_unauthenticated(self):
        if self.c is None:
            self.c = JIRA(options={'server': self.conf.site.url})

        logger.info("creating an unauthenticated jira connection.")

    def comments(self, issue):
        return self.c.comments(issue)

    def update_version_cache(self, project):
        versions = self.c.project_versions(project)

        for ver in versions:
            logger.debug("adding '{0}' to version cache".format(ver.name))

            if project not in self.versions_cache:
                self.versions_cache[project] = {}

            self.versions_cache[project][ver.name] = ver.id

    def create_issue(self, title, text, assignee, project, reporter=None,
                     tags=None, version=None, uid=None):
        issue = {'project': {'key': project},
                 'issuetype': {'name': 'Task'},
                 'summary': title,
                 'description': text,
                 'assignee': {'name': assignee}}

        if reporter is not None:
            issue['reporter'] = {'name': reporter}
        if tags is not None:
            issue['labels'] = [tags]
        if version is not None:
            if project not in self.versions_cache:
                logger.debug("updating version cache to include {0} versions".format(project))
                self.update_version_cache(project)

            if version not in self.versions_cache[project]:
                logger.error("version {0} doesn't exist in {1} project".format(version, project))
            else:
                issue['fixVersions'] = [{'id': self.versions_cache[project][version]}]
                logger.debug('adding version to issue: {0}'.format(issue['fixVersions']))

        new_issue = self.c.create_issue(fields=issue)

        logger.debug('created new issue {0}'.format(new_issue.key))
        self.issues_created.append({'key': new_issue.key,
                                    'uid': uid,
                                    'title': title})

    def query(self, query_string):
        logger.info('running query for: {0}'.format(query_string))
        try:
            query_results = self.c.search_issues(jql_str=query_string,
                                                 maxResults=200)
        except Exception as e:
            logger.warning(query_string)
            logger.error(e)
            if self.abort_on_error is True:
                raise SystemExit(e)

        if self.results_format == 'dict':
            return {issue.key: issue for issue in query_results}
        elif self.results_format == 'list':
            return [issue for issue in query_results]

    def components(self, project):
        return self.c.project_components(project)

    def versions(self, project, released=False, archived=False):
        return [v
                for v in self.c.project_versions(project)
                if v.released is released and v.archived is archived
                ]

    def release_version(self, version):
        if not isinstance(version, Version):
            logger.error('{0} is not a jira version.'.format(version))
        else:
            logger.info('releasing version {0}'.format(version.name))
            version.update(released=True)

    def archive_version(self, version):
        if not isinstance(version, Version):
            logger.error('{0} is not a jira version.'.format(version))
        else:
            logger.info('archiving version {0}'.format(version.name))
            version.update(archived=True)

    def create_version(self, project, name, description='', release=None):
        if release is None:
            release = str(datetime.date.today() + datetime.timedelta(days=14))
        elif release is False:
            release = None
        elif isinstance(release, datetime.date):
            release = str(release)

        self.c.create_version(name=name,
                              project=project,
                              description=description,
                              releaseDate=release)

        logger.debug('created version {0} in project {0}'.format(name, project))
