# -*- coding: utf-8 -*-
#
#  _____         _____ _           _
# |   __|___ _ _|_   _| |_ ___ ___| |_ ___
# |__   | .'| | | | | |   | .'|   | '_|_ -|
# |_____|__,|_  | |_| |_|_|__,|_|_|_,_|___|
#           |___|

import logging
import os
import json
import requests
import time  # Added to handle timestamping for audio filenames

# Import your get_version function
from .version import get_version
from .utils import strip_html

from functools import wraps
from flask import Flask, request, session, render_template, url_for
from flask import abort, redirect, Markup, make_response
from flask import send_from_directory
from flask_common import Common
from names import get_full_name
from raven.contrib.flask import Sentry
from flask_qrcode import QRcode
from . import storage
from urllib.parse import quote, unquote
from lxml_html_clean import Cleaner
from markdown import markdown
from werkzeug.utils import secure_filename

cleaner = Cleaner()
cleaner.javascript = True
cleaner.style = True
cleaner.remove_tags = ['script', 'style', 'link']
cleaner.allow_attributes = ['alt', 'href']
cleaner.remove_attributes = [
    'id',
    'class',
    'style',
    'align',
    'border',
    'cellpadding',
    'cellspacing',
    'width',
    'height',
    'hspace',
    'vspace',
    'frameborder',
    'marginwidth',
    'marginheight',
    'noresize',
    'scrolling',
    'target',
    'onclick',
    'ondblclick',
    'onmousedown',
    'onmousemove',
    'onmouseover',
    'onmouseout',
    'onmouseup',
    'onkeypress',
    'onkeydown',
    'onkeyup',
    'onblur',
    'onchange',
    'onfocus',
    'onselect',
    'onreset',
    'onsubmit',
    'onabort',
    'oncanplay',
    'oncanplaythrough',
    'oncuechange',
    'ondurationchange',
    'onemptied',
    'onended',
    'onloadeddata',
    'onloadedmetadata',
    'onloadstart',
    'onpause',
    'onplay',
    'onplaying',
    'onprogress',
    'onratechange',
    'onseeked',
    'onseeking',
    'onstalled',
    'onsuspend',
    'ontimeupdate',
    'onvolumechange',
    'onwaiting',
]


def remove_tags(html):
    return cleaner.clean_html(html)


# importing module

# Create and configure logger
logging.basicConfig(
    filename='Logfile.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
)

# Creating an object
logger = logging.getLogger()

# Application Basics
# ------------------

app = Flask(__name__)
app.config['APP_VERSION'] = get_version()
app.config['FB_APP_ID'] = os.environ.get('FB_APP_ID', '1390341129685401')

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

@app.route("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")


@app.route('/privacy')
def privacy():
    return render_template("privacy.htm.j2")


@app.route('/')
def index():
    if 'search_str' in session:
        session.pop('search_str', None)

    return render_template(
        'index.htm.j2',
        callback_url=auth_callback_url,
        auth_id=auth_id,
        auth_domain=auth_domain,
    )


@app.route('/inbox', methods=['GET'])
@requires_auth
def inbox():
    """Handle GET requests to display the inbox."""
    # Auth0 stored account information.
    profile = session['profile']
    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])
    is_enabled = storage.Inbox.is_enabled(inbox_db.slug)
    is_email_enabled = storage.Inbox.is_email_enabled(inbox_db.slug)

    # pagination
    page = request.args.get('page', 1, type=int)
    page_size = 25

    # checking for invalid page numbers
    if page < 0:
        return render_template("404notfound.htm.j2")

    # Get search string from session if it exists
    search_str = session.get('search_str')

    # Get appropriate data based on search status
    if search_str:
        data = inbox_db.search_notes(search_str, page, page_size)
    else:
        data = inbox_db.notes(page, page_size)
        search_str = "Search by message body or byline"

    if page > data['total_pages'] and data['total_pages'] != 0:
        return render_template("404notfound.htm.j2")

    return render_template(
        "inbox.htm.j2",
        user=profile,
        notes=data["notes"],
        inbox=inbox_db,
        is_enabled=is_enabled,
        is_email_enabled=is_email_enabled,
        page=data["page"],
        total_pages=data["total_pages"],
        search_str=search_str,
    )


@app.route('/inbox/search', methods=['POST'])
@requires_auth
def inbox_search():
    """Handle POST requests for search operations."""
    if 'clear' in request.form:
        session.pop('search_str', None)
    else:
        session['search_str'] = request.form['search_str']
    return redirect(url_for('inbox'))


@app.route('/inbox/export/<export_format>')
@requires_auth
def inbox_export(export_format):

    # Auth0 stored account information.
    profile = session['profile']

    # Grab the inbox from the database.
    inbox_db = storage.Inbox(profile['nickname'])

    # Send over the list of all given notes for the user.
    response = make_response(inbox_db.export(export_format))
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
    return render_template(
        'inbox_archived.htm.j2',
        user=profile,
        notes=inbox_db.archived_notes,
        inbox=inbox_db,
        is_enabled=is_enabled,
        is_email_enabled=is_email_enabled,
    )


@app.route('/thanks')
def thanks():
    return render_template(
        'thanks.htm.j2',
        callback_url=auth_callback_url,
        auth_id=auth_id,
        auth_domain=auth_domain,
    )


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


@app.route('/to/<inbox_id>', methods=['GET'], defaults={"topic": ""})
@app.route('/to/<inbox_id>&<topic>', methods=['GET'])
def display_submit_note(inbox_id, topic):
    """Display a web form in which user can edit and submit a note."""
    if not storage.Inbox.does_exist(inbox_id):
        abort(404)
    elif not storage.Inbox.is_enabled(inbox_id):
        abort(404)

    print("topic received:", topic if topic else "No topic provided")

    fake_name = get_full_name()
    raw_topic = topic
    # URL decode the topic if it was encoded
    if raw_topic:
        raw_topic = unquote(raw_topic)
    display_topic = ""
    if raw_topic:
        display_topic = " about " + raw_topic
    return render_template(
        'submit_note.htm.j2',
        user=inbox_id,
        topic=display_topic,
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


def clean_topic(t):
    if not t:
        return None
    return t.replace(' about ', '')


# Allowed audio extensions and a MIME fallback map for browsers (notably iOS
# Safari) that send filename="blob" or an extensionless name.
ALLOWED_AUDIO_EXT = {'.m4a', '.mp4', '.webm', '.ogg', '.oga', '.mp3', '.wav', '.aac', '.caf'}
MIME_TO_EXT = {
    'audio/mp4': '.m4a',
    'video/mp4': '.m4a',
    'audio/aac': '.m4a',
    'audio/x-m4a': '.m4a',
    'audio/webm': '.webm',
    'audio/ogg': '.ogg',
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/x-caf': '.caf',
}

# Table/image styling injected ahead of rendered Markdown.
TABLE_STYLE = """
<style>
table { width: 100%; table-layout: fixed; border-collapse: collapse; }
th, td { padding: 8px; border: 1px solid #ddd; word-break: break-word;
         max-width: 300px; vertical-align: top; }
td.message-cell { max-width: 500px; overflow-x: hidden; }
td.message-cell img { max-width: 100% !important; height: auto !important;
                      display: block; margin: 10px auto; }
td.message-cell p { margin: 0; padding: 0; }
.ellipsis { white-space: normal; overflow-wrap: break-word; }
</style>
"""


def _save_audio_upload(inbox_id):
    """Persist an uploaded voice note and return its stored filename.

    Returns None when no usable audio was supplied or the save failed.
    """
    audio_file = request.files.get('audio')

    # A file input that was never touched still sends an empty part in a
    # native multipart POST, so an empty .filename must be treated as "no audio".
    if not audio_file or not audio_file.filename:
        logging.info("submit_note: no audio part in request")
        return None

    raw_name = secure_filename(audio_file.filename) or 'voice_note'
    _root, ext = os.path.splitext(raw_name)
    ext = ext.lower()

    if ext not in ALLOWED_AUDIO_EXT:
        mimetype = (audio_file.mimetype or '').split(';')[0].strip().lower()
        ext = MIME_TO_EXT.get(mimetype, '.m4a')
        logging.info(
            "submit_note: normalising audio name %r (mime=%r) -> ext %s",
            audio_file.filename, mimetype, ext,
        )

    upload_folder = os.path.join(app.static_folder, 'recordings')
    os.makedirs(upload_folder, exist_ok=True)

    audio_filename = f"{secure_filename(inbox_id) or 'inbox'}_{int(time.time())}{ext}"
    save_path = os.path.join(upload_folder, audio_filename)

    logging.info("submit_note: saving audio to %s", save_path)
    try:
        audio_file.save(save_path)
    except Exception as e:
        logging.exception("submit_note: failed to save audio file: %s", e)
        return None

    size = os.path.getsize(save_path) if os.path.exists(save_path) else 0
    if size == 0:
        logging.error("submit_note: audio file saved but is empty, discarding: %s", save_path)
        try:
            os.remove(save_path)
        except OSError:
            pass
        return None

    # NOTE: the original code logged an undefined name `filename` here, raising
    # NameError which the surrounding except reset audio_filename to None.
    # That is why saved recordings never reached the email (issue #287).
    logging.info("Audio file saved successfully: %s (%d bytes)", audio_filename, size)
    return audio_filename


def _recipient_email(inbox_db):
    """Resolve the notification address for an inbox.

    `session` may be non-empty without holding a profile (for example when
    `search_str` is set), so the profile is probed explicitly rather than
    relying on the truthiness of `session`.
    """
    email_address = (session.get('profile') or {}).get('email')
    if not email_address:
        email_address = storage.Inbox.get_email(inbox_db.slug)
    return email_address

@app.route('/to/<inbox_id>/submit', methods=['POST'], defaults={"topic": None})
@app.route('/to/<inbox_id>/submit/<topic>', methods=['POST'])
def submit_note(inbox_id, topic):
    """Store note in database and send a copy to user's email."""
    logging.info(
        "submit_note ENTER inbox=%s topic=%r form_keys=%s file_keys=%s "
        "content_length=%s ua=%s",
        inbox_id, topic, list(request.form.keys()), list(request.files.keys()),
        request.content_length, request.headers.get('User-Agent'),
    )

    # Reject unknown or disabled inboxes rather than failing later on auth_id lookup.
    if not storage.Inbox.does_exist(inbox_id):
        logging.error("submit_note: inbox does not exist: %s", inbox_id)
        abort(404)
    if not storage.Inbox.is_enabled(inbox_id):
        logging.error("submit_note: inbox is disabled: %s", inbox_id)
        abort(404)

    inbox_db = storage.Inbox(inbox_id)

    # ---- AUDIO UPLOAD HANDLING ----
    audio_filename = _save_audio_upload(inbox_id)

    # ---- FORM FIELDS ----
    # Use .get() throughout: a missing key on request.form raises a Werkzeug 400
    # before any application logging runs, which makes the failure invisible in
    # Logfile.log. This was the symptom reported for iOS Safari submissions.
    raw_body = request.form.get('body', '')
    content_type = (request.form.get('content-type') or 'markdown').lower()
    byline = Markup(request.form.get('byline') or '').striptags().strip()

    if not raw_body.strip():
        logging.error(
            "submit_note: EMPTY BODY, discarding submission. form=%s files=%s",
            dict(request.form), list(request.files.keys()),
        )
        # Pretend that it was successful (matches historical behaviour).
        return redirect(url_for('thanks'))

    if not byline:
        byline = 'Anonymous'

    topic = clean_topic(topic)

    # ---- BODY PREPARATION ----
    if content_type == 'html':
        # Sanitize attacker-controlled HTML before marking it safe.
        # The submission endpoint is unauthenticated and the stored body is
        # later rendered through {{ note.body|safe }} in inbox.htm.j2 and also
        # embedded into the HTML email sent to the inbox owner (myemail.py).
        # Without sanitization a POST with content-type=html and
        # body=<script>...</script> stores an exploit that fires when the owner
        # opens /inbox or the notification email - full session takeover via
        # document.cookie since the Auth0 cookies are not HttpOnly.
        html_cleaner = Cleaner(
            scripts=True, javascript=True, embedded=True, frames=True,
            forms=True, meta=True, links=False, page_structure=True,
            processing_instructions=True, style=True,
            safe_attrs_only=True, remove_unknown_tags=True,
        )
        body = Markup(html_cleaner.clean_html(raw_body))
    else:
        body = TABLE_STYLE + markdown(raw_body, extensions=['tables', 'fenced_code'])

    # ---- STORE ----
    try:
        submitted_note = inbox_db.submit_note(
            body=body, byline=byline, audio_path=audio_filename
        )
    except Exception as e:
        logging.exception("submit_note: failed to store note: %s", e)
        abort(500)

    logging.info(
        "submit_note: stored uuid=%s audio=%s", submitted_note.uuid, audio_filename
    )

    # ---- NOTIFY ----
    # A failed email must never lose an already-stored note.
    try:
        if storage.Inbox.is_email_enabled(inbox_db.slug):
            email_address = _recipient_email(inbox_db)
            if email_address:
                submitted_note.notify(email_address, topic, audio_filename)
                logging.info(
                    "submit_note: notification dispatched to %s (audio=%s)",
                    email_address, audio_filename,
                )
            else:
                logging.error(
                    "submit_note: no recipient address for inbox %s", inbox_db.slug
                )
        else:
            logging.info("submit_note: email disabled for inbox %s", inbox_db.slug)
    except Exception as e:
        logging.exception("submit_note: notification failed for uuid=%s: %s",
                          submitted_note.uuid, e)

    return redirect(url_for('thanks'))


@app.route('/logout', methods=["POST"])
def user_logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/callback')
def callback_handling():
    code = request.args.get('code')

    json_header = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {auth_jwt_v2}',
    }

    token_url = f'https://{auth_domain}/oauth/token'
    token_payload = {
        'client_id': auth_id,
        'client_secret': auth_secret,
        'redirect_uri': auth_callback_url,
        'code': code,
        'grant_type': 'authorization_code',
    }

    # Fetch User info from Auth0.
    token_info = requests.post(
        token_url, data=json.dumps(token_payload), headers=json_header
    ).json()
    user_url = (
        f'https://{auth_domain}/userinfo?access_token={token_info["access_token"]}'
    )
    user_info = requests.get(user_url).json()

    user_info_url = f'https://{auth_domain}/api/v2/users/{user_info["sub"]}'

    user_detail_info = requests.get(user_info_url, headers=json_header).json()

    # Add the 'user_info' to Flask session.
    session['profile'] = user_info

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
