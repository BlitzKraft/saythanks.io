# -*- coding: utf-8 -*-

#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|


# Application Basics
# ------------------

import jwt
import base64
import os

from functools import wraps
from flask import Flask, request, jsonify, _request_ctx_stack, render_template
from uuid import uuid4
from functools import wraps

app = Flask(__name__)
app.secret_key = 'CHANGEME'

client_id = 'igVLaJdbA3MeUFa416Jad65JN2mZVyaB'
client_secret = 'YGsf-9XYZyEVmLxisj8wOiJDnYuNHVYMXqYFGJEz9VtdyquSJkLMFlNUY8OVejwB'

def handle_error(error, status_code):
  resp = jsonify(error)
  resp.status_code = status_code
  return resp

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth:
            return handle_error({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'}, 401)

        parts = auth.split()

        if parts[0].lower() != 'bearer':
            return handle_error({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}, 401)
        elif len(parts) == 1:
            return handle_error({'code': 'invalid_header', 'description': 'Token not found'}, 401)
        elif len(parts) > 2:
            return handle_error({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}, 401)

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                base64.b64decode(client_secret.replace("_","/").replace("-","+")),
                audience=client_id
            )
        except jwt.ExpiredSignature:
            return handle_error({'code': 'token_expired', 'description': 'token is expired'}, 401)
        except jwt.InvalidAudienceError:
            return handle_error({'code': 'invalid_audience', 'description': 'incorrect audience, expected: ' + client_id}, 401)
        except jwt.DecodeError:
            return handle_error({'code': 'token_invalid_signature', 'description': 'token signature is invalid'}, 401)
        except Exception:
            return handle_error({'code': 'invalid_header', 'description':'Unable to parse authentication token.'}, 400)

        _request_ctx_stack.top.current_user = user = payload
        return f(*args, **kwargs)

    return decorated



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


@app.route('/ping')
def ping():
    return "All good. You don't need to be authenticated to call this"


@app.route("/secured/ping")
@requires_auth
def securedPing():
    return "All good. You only get this message if you're authenticated"

@app.route('/callback', methods=['POST'])
def display_auth():
    token = request.form
    return jsonify(token=token)



