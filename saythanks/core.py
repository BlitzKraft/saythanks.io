# -*- coding: utf-8 -*-

#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|


# Application Basics
# ------------------

from flask import Flask, request, render_template, session
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'CHANGEME'


# Application Security
# --------------------

# CSRF Protection.
@app.before_request
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


# Application Routes
# ------------------

@app.route('/')
def index():
    return render_template('index.htm.j2')

# Application Routes
# ------------------

@app.route('/register')
def registration():
    return render_template('register.htm.j2')


