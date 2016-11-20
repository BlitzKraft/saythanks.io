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
from flask import Flask, request, session, render_template, abort, redirect

from . import storage

# Application Basics
# ------------------


app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'CHANGEME')
app.debug = True


# Application Security
# --------------------

# CSRF Protection.
# @app.before_request
def csrf_protect():
    """Blocks incoming POST requests if a proper CSRF token is not provided."""
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


def generate_csrf_token():
    """Generates a CSRF token."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = str(uuid4())
    return session['_csrf_token']


# Register the CSRF token with jinja2.
app.jinja_env.globals['csrf_token'] = generate_csrf_token


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
    return render_template('index.htm.j2')


@app.route('/register')
def registration():
    return render_template('register.htm.j2',
        callback_url=auth_callback_url,
        auth_id=auth_id,
        auth_domain=auth_domain
    )

@app.route('/home')
@requires_auth
def dashboard():
    return render_template('about.htm.j2', user=session['profile'])

@app.route('/<inbox>')
@requires_auth
def public_inbox(inbox):
    return render_template('about.htm.j2', user=session['profile'])



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

    if is not storage.Inbox.is_linked(userid):
        # Using nickname by default, can be changed manually later if needed.
        storage.Inbox.store(nickname, userid)

    return redirect('/home')
