import requests
import logging

from requests.auth import HTTPDigestAuth

from giza.config.credentials import CredentialsConfig

logger = logging.getLogger('giza.corp')


def corp_api_call(endpoint, conf):
    credentials = CredentialsConfig(conf.site.credentials).corp

    url = conf.site.corp + '/api/' + endpoint
    headers = {'accept': 'application/json'}
    response = requests.get(url,
                            auth=HTTPDigestAuth(credentials.username, credentials.password),
                            headers=headers)

    return response.json()


def get_contributor_list(conf):
    contributors = corp_api_call('contributors', conf)['contributors']

    c_github = list({str(c['github_username']) for c in contributors
                     if ('github_username' in c and
                         c['github_username'] is not None and
                         c['github_username'] != u'')})

    return c_github
