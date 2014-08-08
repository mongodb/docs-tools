# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib

from bson import json_util
from flask import request, url_for

from flask_app import app
import models


def to_json(value):
    ''' This filter converts value to json
    :param string value: string to convert to json
    :returns: The json version of the string
    '''
    return json.dumps(value, default=json_util.default)


def pathname2url(path):
    ''' This filter convert a path to a file to a url
    :param string path: path to a file
    :returns: The string of the path
    '''
    return urllib.pathname2url(path)


def check_if_user_approved(user, sentenceID):
    ''' This filter checks if the user approved the sentence
    :param string user: the user's username
    :param string sentenceID: the sentence's id
    :returns: a boolean saying if the user approved the sentence
    '''
    s = models.Sentence(oid=sentenceID)
    return models.User(username=user)._id in s.state['approvers']


def check_if_user_edited(user, sentenceID):
    ''' This filter checks if the user edited the sentence
    :param string user: the user
    :param string sentenceID: the sentence's id
    :returns: a boolean saying if the user edited the sentence
    '''
    s = models.Sentence(oid=sentenceID)
    return models.User(username=user)._id == s.state['userID']


def get_userID(user):
    ''' This filter gets userID of a user
    :Parameters:
        - 'user': the user
    :Returns:
        - userID
    '''
    return models.User(username=user)._id


def list_length(l):
    ''' This filter gets the length of a list
    :param list l: the list
    :returns: length of the list
    '''
    return len(l)


def url_for_other_page(page):
    ''' This filter gets the url for another page
    :param string page: the name of the page
    :returns: url for the page
    '''
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.filters['to_json'] = to_json
app.jinja_env.filters['pathname2url'] = pathname2url
app.jinja_env.filters['check_if_user_approved'] = check_if_user_approved
app.jinja_env.filters['check_if_user_edited'] = check_if_user_edited
app.jinja_env.filters['get_userID'] = get_userID
app.jinja_env.filters['list_length'] = list_length
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
