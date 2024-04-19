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

from functools import wraps
from flask import Flask, request, session, render_template, url_for
from flask import abort, redirect, make_response
from markupsafe import Markup
from names import get_full_name
from raven.contrib.flask import Sentry
from flask_qrcode import QRcode
from . import storage
from urllib.parse import quote
from lxml_html_clean import Cleaner
from markdown import markdown
from kinde_sdk.kinde_api_client import GrantType, KindeApiClient
from kinde_sdk import Configuration

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

# to encode a query
app.jinja_env.filters['quote'] = quote

QRcode(app)
app.secret_key = os.environ.get('APP_SECRET', 'CHANGEME')
app.debug = True

# Sentry for catching application errors in production.
if 'SENTRY_DSN' in os.environ:
    sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])

# Kinde Integration
# -----------------

configuration = Configuration(host=os.environ['KINDE_CONFIGURATION'])

kinde_api_client_params = {
    "configuration": configuration,
    "domain": os.environ['KINDE_CONFIGURATION'] ,
    "client_id": os.environ['KINDE_CLIENT_ID'],
    "client_secret": os.environ['KINDE_CLIENT_SECRET'],
    "grant_type": GrantType.AUTHORIZATION_CODE,
    "callback_url": os.environ['KINDE_CALLBACK_URL']
}

kinde_client = KindeApiClient(**kinde_api_client_params)

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
    return render_template('index.htm.j2')


@app.route("/login")
def login():
    return app.redirect(kinde_client.get_login_url())


@app.route("/register")
def register():
    return app.redirect(kinde_client.get_register_url())


@app.route('/inbox', methods=['POST', 'GET'])
@requires_auth
def inbox():
    # Kinde stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])
    is_enabled = storage.Inbox.is_enabled(inbox_db.slug)

    is_email_enabled = storage.Inbox.is_email_enabled(inbox_db.slug)
    if request.method == "GET":
        # Send over the list of all given notes for the user.
        return render_template('inbox.htm.j2',
                            user=profile, notes=inbox_db.notes,
                            inbox=inbox_db, is_enabled=is_enabled,
                            is_email_enabled=is_email_enabled)
    search_str = request.form['search_str']
    return render_template('inbox.htm.j2',
                        user=profile, notes=inbox_db.search_notes(search_str),
                        is_email_enabled=is_email_enabled)
        


@app.route('/inbox/export/<format>')
@requires_auth
def inbox_export(format):

    # Kinde stored account information.
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

    # Kinde stored account information.
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
    return render_template('thanks.htm.j2')


@app.route('/disable-email')
@requires_auth
def disable_email():
    # Kinde stored account information.
    slug = session['profile']['email']
    storage.Inbox.disable_email(slug)
    return redirect(url_for('inbox'))


@app.route('/enable-email')
@requires_auth
def enable_email():
    # Kinde stored account information.
    slug = session['profile']['email']
    storage.Inbox.enable_email(slug)
    return redirect(url_for('inbox'))


@app.route('/disable-inbox')
@requires_auth
def disable_inbox():
    # Kinde stored account information.
    slug = session['profile']['email']
    storage.Inbox.disable_account(slug)
    return redirect(url_for('inbox'))


@app.route('/enable-inbox')
@requires_auth
def enable_inbox():
    # Kinde stored account information.
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
    return render_template('share_note.htm.j2', note=note)


@app.route('/inbox/archive/note/<uuid>', methods=['GET'])
@requires_auth
def archive_note(uuid):
    """Set aside the note by moving it into an archive."""
    # Kinde stored account information.
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
    kinde_client.fetch_token(authorization_response=request.url)
    if kinde_client.is_authenticated():
        user_detail_info = kinde_client.get_user_details()
        session['profile'] = user_detail_info
        nickname = user_detail_info['email'].split('@')[0]
        email = user_detail_info['email']
        userid = user_detail_info['id']
        picture = user_detail_info['picture']
        name = user_detail_info['given_name']+" "+user_detail_info['family_name']
        session['profile']['nickname'] = nickname
        session['profile']['picture'] = picture
        session['profile']['name'] = name
        if not storage.Inbox.does_exist(nickname):
            # Using nickname by default, can be changed manually later if needed.
            storage.Inbox.store(nickname, userid, email)
        return redirect(url_for('inbox'))
    else:
        return "Error : Unable to login"
    