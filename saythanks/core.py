# -*- coding: utf-8 -*-

#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|

from crypt import methods
import os
import json
import requests

from functools import wraps
from flask import Flask, request, session, render_template, url_for
from flask import abort, redirect, Markup, make_response
from flask_common import Common
from names import get_full_name
from raven.contrib.flask import Sentry
from flask_qrcode import QRcode
from . import storage


# Application Basics
# ------------------

app = Flask(__name__)
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
    return render_template('index.htm.j2',
                           callback_url=auth_callback_url,
                           auth_id=auth_id,
                           auth_domain=auth_domain)


@app.route('/inbox')
@requires_auth
def inbox():

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])

    is_enabled = storage.Inbox.is_enabled(inbox_db.slug)

    is_email_enabled = storage.Inbox.is_email_enabled(inbox_db.slug)

    # Send over the list of all given notes for the user.
    return render_template('inbox.htm.j2',
                           user=profile, notes=inbox_db.notes,
                           inbox=inbox_db, is_enabled=is_enabled,
                           is_email_enabled=is_email_enabled)


@app.route('/inbox/export/<format>')
@requires_auth
def inbox_export(file_format):

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])

    # Send over the list of all given notes for the user.
    response = make_response(inbox_db.export(file_format))
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
        abort(404)

    note = storage.Note.fetch(uuid)

    return render_template('share_note.htm.j2', note=note)


@app.route('/inbox/archive/note/<uuid>', methods=['GET'])
@requires_auth
def archive_note(uuid):
    """Set aside the note by moving it into an archive."""
    # Auth0 stored account information.
    profile = session['profile']

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

        return redirect(url_for('thanks'))
    else:
        # Strip any HTML away.
        body = Markup(body).striptags()
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
                   'Authorization': 'Bearer {0}'.format(auth_jwt_v2)}

    token_url = 'https://{0}/oauth/token'.format(auth_domain)
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
    user_url = 'https://{0}/userinfo?access_token={1}'.format(
        auth_domain, token_info['access_token'])
    user_info = requests.get(user_url).json()

    user_info_url = 'https://{0}/api/v2/users/{1}'.format(
        auth_domain, user_info['sub'])

    user_detail_info = requests.get(user_info_url, headers=json_header).json()
    # print(f"user_info:{user_info}, user_detail_info:{user_detail_info}")
    print("user_url", user_url)
    print("user_info_url", user_info_url)
    print(f"user_info: {user_info}")
    print(f"user_detail_info: {user_detail_info}")

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
