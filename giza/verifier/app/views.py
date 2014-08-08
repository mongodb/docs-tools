import json
import logging
import urllib
from math import ceil

from bson import json_util
from flask import  request, redirect, render_template
from flask_app import app, db

import models

logger = logging.getLogger('verifier.app.views')


@app.route('/')
@app.route('/index')
def language_picker():
    ''' This view shows the valid languages '''
    languages = models.get_languages()
    return render_template("language_picker.html",
                           language_list=languages)


@app.route('/file/<username>/<language>/', defaults={'page': 1})
@app.route('/file/<username>/<language>/page/<int:page>/')
def file_browser(language, username, page):
    ''' This view shows the valid files
    :param string language: the current target language
    :param string username: the current user
    '''
    files = models.get_fileIDs('en', language)
    num_files = files.count()
    page_files = models.get_files_for_page(page, app.config['NUM_FILES_PER_PAGE'], files)
    pagination = Pagination(page, app.config['NUM_FILES_PER_PAGE'], num_files)
    return render_template("file_browser.html",
                           file_list=page_files,
                           language=language,
                           username=username,
                           pagination=pagination)


@app.route('/file/<username>/<language>/<path:file>')
def file_editor(file, language, username):
    ''' This view shows the sentences in a file to edit
    :param string file': the file currently being edited
    :param string language': the current target language
    :param string username': the current user
    '''
    if file[-1] == '/':
        file = file[:-1]
    f = models.File(oid=models.find_file("en", language, file)['_id'])
    u = models.User(username=username)
    if f.grab_lock(u._id) is False:
        return redirect('/file/{0}/{1}/{2}/423'.format(username, language, file))

    sentences = models.get_sentences_in_file(urllib.url2pathname(file), 'en', language)
    return render_template('file_editor.html',
                           sentence_list=sentences,
                           language=language,
                           username=username)


@app.route('/add', methods=['POST'])
def edit_translation():
    ''' This function is called when a user posts an edit.
    It first validates the edit and then it it submits it to the database
    '''
    try:
        j = fix_json(request.json)
        t = models.Sentence(oid=j[u'old'][u'_id'])
        editor = models.User(username=j[u'new'][u'editor'])
        t.edit(editor, j[u'new'][u'new_target_sentence'])
        return json.dumps({"code": 200, "msg": "Edit Succeeded"}), 200
    except KeyError:
        return json.dumps({"code": 401, "msg": "Edit Failed"}), 500
    except models.MyError as e:
        return json.dumps({"code": e.code, "msg": e.msg}), e.code
    except models.LockError as e:
        return json.dumps({"code": e.code, "msg": e.msg, "file_path": e.file_path,
                           "username": e.username, "target_language": e.target_language}), e.code


@app.route('/approve', methods=['POST'])
def approve_translation():
    ''' This function is called when a user approves a sentence.
    It first validates the approval and then it it submits it to the database
    '''
    j = fix_json(request.json)
    t = models.Sentence(oid=j[u'old'][u'_id'])
    approver = models.User(username=j[u'new'][u'approver'])
    try:
        t.approve(approver)
        return json.dumps({"code:": 200, "msg": "Approval Succeeded"}), 200
    except models.MyError as e:
        return json.dumps({"code": e.code, "msg": e.msg}), e.code
    except models.LockError as e:
        return json.dumps({"code": e.code, "msg": e.msg, "file_path": e.file_path,
                           "username": e.username, "target_language": e.target_language}), e.code


@app.route('/unapprove', methods=['POST'])
def unapprove_translation():
    ''' This function is called when a user posts an edit.
    It first validates the edit and then it it submits it to the database
    '''
    j = fix_json(request.json)
    t = models.Sentence(oid=j[u'old'][u'_id'])
    unapprover = models.User(username=j[u'new'][u'unapprover'])
    try:
        t.unapprove(unapprover)
        return json.dumps({"code:": 200, "msg": "Unapproval Succeeded"}), 200
    except models.MyError as e:
        return json.dumps({"code": e.code, "msg": e.msg}), e.code
    except models.LockError as e:
        return json.dumps({"code": e.code, "msg": e.msg, "file_path": e.file_path,
                           "username": e.username, "target_language": e.target_language}), e.code


@app.route('/file/<username>/<language>/<path:file>/423')
def lock_error(username, language, file):
    return render_template("423.html",
                           username=username,
                           language=language,
                           file=file)


def fix_json(json_object):
    ''' helper function to fix json from request for mongodb
    :param json json_object: some json object
    :returns: a better json object
    '''
    return json.loads(json.dumps(json_object, default=json_util.default), object_hook=json_util.object_hook)


class Pagination(object):
    '''This class creates pages for the views so that it doesn't need to show
    all files or sentences at once'''
    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        '''This method creates an iterator for the pages to show at the bottom of the page
        :param string left_edge: how many numbers are shown on the left edge of the page list
        :param string left_current: how many numbers are shown left of the current page
        :param string right_current: how many numbers are shown right of the current page
        :param string right_edge: how many numbers are shown on the right edge of the page list
        :returns: iterator over the page numbers
        '''
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
                num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
