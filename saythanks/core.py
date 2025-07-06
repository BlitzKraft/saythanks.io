# -*- coding: utf-8 -*-

#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|

import logging
import os
import json
import requests
# Import your get_version function
from .version import get_version
from .utils import strip_html

from functools import wraps
from flask import Flask, request, session, render_template, url_for
from flask import abort, redirect, Markup, make_response
from flask_common import Common
from names import get_full_name
from raven.contrib.flask import Sentry
from flask_qrcode import QRcode
from . import storage
from urllib.parse import quote
from lxml_html_clean import Cleaner
from markdown import markdown

cleaner = Cleaner()
cleaner.javascript = True
cleaner.style = True
cleaner.remove_tags = ['script', 'style', 'link']
cleaner.allow_attributes = ['alt', 'href']
cleaner.remove_attributes = ['id', 'class', 'style', 'align', 'border', 'cellpadding', 'cellspacing', 'width', 'height', 'hspace', 'vspace', 'frameborder', 'marginwidth', 'marginheight', 'noresize', 'scrolling', 'target', 'onclick', 'ondblclick', 'onmousedown', 'onmousemove', 'onmouseover', 'onmouseout', 'onmouseup', 'onkeypress', 'onkeydown', 'onkeyup', 'onblur',
                             'onchange', 'onfocus', 'onselect', 'onreset', 'onsubmit', 'onabort', 'oncanplay', 'oncanplaythrough', 'oncuechange', 'ondurationchange', 'onemptied', 'onended', 'onloadeddata', 'onloadedmetadata', 'onloadstart', 'onpause', 'onplay', 'onplaying', 'onprogress', 'onratechange', 'onseeked', 'onseeking', 'onstalled', 'onsuspend', 'ontimeupdate', 'onvolumechange', 'onwaiting']


def remove_tags(html):
    return cleaner.clean_html(html)


# importing module

# Create and configure logger
logging.basicConfig(filename='Logfile.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

# Creating an object
logger = logging.getLogger()

# Application Basics
# ------------------

app = Flask(__name__)
app.config['APP_VERSION'] = get_version()

# to encode a query
app.jinja_env.filters['quote'] = quote

# to strip html formatting
app.jinja_env.filters['strip_html'] = strip_html

QRcode(app)
app.secret_key = os.environ.get('APP_SECRET', 'CHANGEME')
app.debug = True

# Flask-Common.
common = Common(app)

# Sentry for catching application errors in production.
if 'SENTRY_DSN' in os.environ:
    sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

# Auth0 Integration
# -----------------

auth_id = os.environ['AUTH0_CLIENT_ID']
auth_secret = os.environ['AUTH0_CLIENT_SECRET']
auth_callback_url = os.environ['AUTH0_CALLBACK_URL']
auth_domain = os.environ['AUTH0_DOMAIN']
auth_jwt_v2 = os.environ['AUTH0_JWT_V2_TOKEN']


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated

# Application Routes
# ------------------


@app.route('/')
def index():
    if 'search_str' in session:
        session.pop('search_str', None)    
    
    return render_template('index.htm.j2',
                           callback_url=auth_callback_url,
                           auth_id=auth_id,
                           auth_domain=auth_domain)


@app.route('/inbox', methods=['POST', 'GET'])
@requires_auth
def inbox():
    # Auth0 stored account information.
    profile = session['profile']
    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])
    is_enabled = storage.Inbox.is_enabled(inbox_db.slug)
    # pagination
    page = request.args.get('page', 1, type=int)
    page_size = 25
    # checking for invalid page numbers
    if page < 0:
        return render_template("404notfound.htm.j2")
    data = inbox_db.notes(page, page_size)
    if page > data['total_pages'] and data['total_pages']!=0:
                return render_template("404notfound.htm.j2")
    is_email_enabled = storage.Inbox.is_email_enabled(inbox_db.slug)

    # handling search with pagination
    if request.method == 'POST':
        if 'clear' in request.form:
            session.pop('search_str', None)
            return redirect(url_for('inbox'))
        session['search_str'] = request.form['search_str']
    # regular note set with pagination
    if request.method == "GET" and 'search_str' not in session:
        # Send over the list of all given notes for the user.
        return render_template('inbox.htm.j2',
                               user=profile, notes=data['notes'],
                               inbox=inbox_db, is_enabled=is_enabled,
                               is_email_enabled=is_email_enabled, page=data['page'],
                               total_pages=data['total_pages'], search_str="Search by message body or byline")
    # reassessing data when search is used
    if 'search_str' in session:
            data = inbox_db.search_notes(session['search_str'], page, page_size)
    return render_template('inbox.htm.j2',
                           user=profile, notes=data['notes'],
                           is_email_enabled=is_email_enabled, page=data['page'],
                           total_pages=data['total_pages'], search_str=session['search_str'])


@app.route('/inbox/export/<format>')
@requires_auth
def inbox_export(format):

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])

    # Send over the list of all given notes for the user.
    response = make_response(inbox_db.export(format))
    response.headers['Content-Disposition'] = 'attachment; filename=saythanks-inbox.csv'
    response.headers['Content-type'] = 'text/csv'
    return response


@app.route('/inbox/archived')
@requires_auth
def archived_inbox():

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])

    is_enabled = storage.Inbox.is_enabled(inbox_db.slug)

    is_email_enabled = storage.Inbox.is_email_enabled(inbox_db.slug)
    # Send over the list of all given notes for the user.
    return render_template('inbox_archived.htm.j2',
                           user=profile, notes=inbox_db.archived_notes,
                           inbox=inbox_db, is_enabled=is_enabled,
                           is_email_enabled=is_email_enabled)


@app.route('/thanks')
def thanks():
    return render_template('thanks.htm.j2',
                           callback_url=auth_callback_url,
                           auth_id=auth_id,
                           auth_domain=auth_domain)


@app.route('/disable-email')
@requires_auth
def disable_email():
    # Auth0 stored account information.
    slug = session['profile']['email']
    storage.Inbox.disable_email(slug)
    return redirect(url_for('inbox'))


@app.route('/enable-email')
@requires_auth
def enable_email():
    # Auth0 stored account information.
    slug = session['profile']['email']
    storage.Inbox.enable_email(slug)
    return redirect(url_for('inbox'))


@app.route('/disable-inbox')
@requires_auth
def disable_inbox():
    # Auth0 stored account information.
    slug = session['profile']['email']
    storage.Inbox.disable_account(slug)
    return redirect(url_for('inbox'))


@app.route('/enable-inbox')
@requires_auth
def enable_inbox():
    # Auth0 stored account information.
    slug = session['profile']['email']
    storage.Inbox.enable_account(slug)
    return redirect(url_for('inbox'))


@app.route('/to/<inbox>', methods=['GET'], defaults={"topic": ""})
@app.route('/to/<inbox>&<topic>', methods=['GET'])
def display_submit_note(inbox, topic):
    """Display a web form in which user can edit and submit a note."""
    if not storage.Inbox.does_exist(inbox):
        abort(404)
    elif not storage.Inbox.is_enabled(inbox):
        abort(404)   
    fake_name = get_full_name()
    topic_string = topic
    if topic_string:
        topic_string = " about " + topic
    return render_template(
        'submit_note.htm.j2',
        user=inbox,
        topic=topic_string,
        fake_name=fake_name)


@app.route('/note/<uuid>', methods=['GET'])
def share_note(uuid):
    """Share and display the note via an unique URL."""
    # Abort if the note is not found.
    if not storage.Note.does_exist(uuid):
        logging.error("Note is not found")
        abort(404)

    note = storage.Note.fetch(uuid)
    note_body = note.body
    for i in ['<div>', '<p>', '</div>', '</p>']:
        note_body = note_body.replace(i, '')
    return render_template('share_note.htm.j2', note=note, note_body=note_body)


@app.route('/inbox/archive/note/<uuid>', methods=['GET'])
@requires_auth
def archive_note(uuid):
    """Set aside the note by moving it into an archive."""
    # Auth0 stored account information.
    # profile = session['profile']

    note = storage.Note.fetch(uuid)

    # Archive the note.
    note.archive()
    # Redirect to the archived inbox.
    return redirect(url_for('archived_inbox'))


@app.route('/to/<inbox>/submit', methods=['POST'])
def submit_note(inbox):
    """Store note in database and send a copy to user's email."""
    # Fetch the current inbox.
    inbox_db = storage.Inbox(inbox)
    body = request.form['body']
    content_type = request.form['content-type']
    byline = Markup(request.form['byline'])

    # If the user chooses to send an HTML email,
    # the contents of the HTML document will be sent
    # as an email but will not be stored due to the enormous size
    # of professional email templates

    if content_type == 'html':
        body = Markup(body)
        note = storage.Note.from_inbox(inbox=None, body=body, byline=byline)
        if storage.Inbox.is_email_enabled(inbox_db.slug):
            # note.notify(email_address)
            if session:
                email_address = session['profile']['email']
            else:
                email_address = storage.Inbox.get_email(inbox_db.slug)
            note.notify(email_address)
        body = remove_tags(body)
        note = inbox_db.submit_note(body=body, byline=byline)
        return redirect(url_for('thanks'))
    # Strip any HTML away.

    body = markdown(body)
    body = remove_tags(body)
    byline = Markup(request.form['byline']).striptags()
    # Assert that the body has length.
    if not body:
        # Pretend that it was successful.
        return redirect(url_for('thanks'))

    # Store the incoming note to the database.
    note = inbox_db.submit_note(body=body, byline=byline)
    # Email the user the new note.
    if storage.Inbox.is_email_enabled(inbox_db.slug):
        # note.notify(email_address)
        if session:
            email_address = session['profile']['email']
        else:
            email_address = storage.Inbox.get_email(inbox_db.slug)
        note.notify(email_address)

    return redirect(url_for('thanks'))


@app.route('/logout', methods=["POST"])
def user_logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/callback')
def callback_handling():
    code = request.args.get('code')

    json_header = {'content-type': 'application/json',
                   'Authorization': f'Bearer {auth_jwt_v2}'}

    token_url = f'https://{auth_domain}/oauth/token'
    token_payload = {
        'client_id': auth_id,
        'client_secret': auth_secret,
        'redirect_uri': auth_callback_url,
        'code': code,
        'grant_type': 'authorization_code'
    }

    # Fetch User info from Auth0.
    token_info = requests.post(token_url, data=json.dumps(
        token_payload), headers=json_header).json()
    user_url = f'https://{auth_domain}/userinfo?access_token={token_info["access_token"]}'
    user_info = requests.get(user_url).json()

    user_info_url = f'https://{auth_domain}/api/v2/users/{user_info["sub"]}'

    user_detail_info = requests.get(user_info_url, headers=json_header).json()

    # Add the 'user_info' to Flask session.
    session['profile'] = user_info

    # nickname = user_info['email']
    nickname = user_detail_info['nickname']
    email = user_detail_info['email']
    userid = user_info['sub']
    picture = user_detail_info['picture']
    name = user_detail_info['name']
    session['profile']['nickname'] = nickname
    session['profile']['picture'] = picture
    session['profile']['name'] = name
    if not storage.Inbox.does_exist(nickname):
        # Using nickname by default, can be changed manually later if needed.
        storage.Inbox.store(nickname, userid, email)
    return redirect(url_for('inbox'))
