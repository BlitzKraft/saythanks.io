# -*- coding: utf-8 -*-

#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|

import os
import json
import requests

from functools import wraps
from uuid import uuid4
from flask import Flask, request, session, render_template, url_for
from flask import abort, redirect

from . import storage

# Application Basics
# ------------------


app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'CHANGEME')
app.debug = True


# Auth0 Integration
# -----------------

auth_id = os.environ['AUTH0_CLIENT_ID']
auth_secret = os.environ['AUTH0_CLIENT_SECRET']
auth_callback_url = os.environ['AUTH0_CALLBACK_URL']
auth_domain = os.environ['AUTH0_DOMAIN']


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


@app.route('/register')
def registration():
    return render_template('register.htm.j2',
        callback_url=auth_callback_url,
        auth_id=auth_id,
        auth_domain=auth_domain
    )


@app.route('/inbox')
@requires_auth
def dashboard():

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox = storage.Inbox(profile['nickname'])

    # Send over the list of all given notes for the user.
    return render_template('about.htm.j2', user=profile, notes=inbox.notes, inbox=inbox)


@app.route('/to/<inbox>', methods=['GET'])
def display_submit_note(inbox):
    if not storage.Inbox.does_exist(inbox):
        abort(404)
    return render_template('submit_note.htm.j2', user=inbox)


@app.route('/to/<inbox>/submit', methods=['POST'])
def submit_note(inbox):

    # Fetch the current inbox.
    inbox = storage.Inbox(inbox)

    # Store the incoming note to the database.
    note = inbox.submit_note(body=request.form['body'], byline=request.form['byline'])

    # Email the user the new note.
    note.notify(inbox.email)

    return "Thanks for being thankful!"


@app.route('/callback')
def callback_handling():
    code = request.args.get('code')

    json_header = {'content-type': 'application/json'}

    token_url = 'https://{0}/oauth/token'.format(auth_domain)
    token_payload = {
        'client_id': auth_id,
        'client_secret': auth_secret,
        'redirect_uri': auth_callback_url,
        'code': code,
        'grant_type': 'authorization_code'
    }

    # Fetch User info from Auth0.
    token_info = requests.post(token_url, data=json.dumps(token_payload), headers=json_header).json()
    user_url = 'https://{0}/userinfo?access_token={1}'.format(auth_domain, token_info['access_token'])
    user_info = requests.get(user_url).json()

    # Add the 'user_info' to Flask session.
    session['profile'] = user_info

    nickname = user_info['nickname']
    userid = user_info['user_id']

    if not storage.Inbox.is_linked(userid):
        # Using nickname by default, can be changed manually later if needed.
        storage.Inbox.store(nickname, userid)

    return redirect(url_for('dashboard'))
