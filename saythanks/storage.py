import os

import records
from auth0.v2.management import Auth0

from . import email

# Auth0 API Client
auth0_domain = os.environ['AUTH0_DOMAIN']
auth0_token = os.environ['AUTH0_JWT_TOKEN']
auth0 = Auth0(auth0_domain, auth0_token)

# Database connection.
db = records.Database()

# Storage Models
# Note: Some of these are a little fancy (send email and such).
# --------------

class Note(object):
    """A generic note of thankfulness."""
    def __init__(self):
        self.body = None
        self.byline = None
        self.inbox = None

    def __repr__(self):
        return '<Note size={}>'.format(len(self.body))

    @classmethod
    def from_inbox(cls, inbox, body, byline):
        """Creates a Note instance from a given inbox."""
        self = cls()

        self.body = body
        self.byline = byline
        self.inbox = Inbox(inbox)

        return self

    def store(self):
        """Stores the Note instance to the database."""
        q = 'INSERT INTO notes (body, byline, inboxes_auth_id) VALUES (:body, :byline, :inbox)'
        r = db.query(q, body=self.body, byline=self.byline, inbox=self.inbox.auth_id)

    def notify(self, email_address):
        # TODO: emails the user when they have received a new note of thanks.
        # get the email address from Auth0

        email.notify(self, email_address)



class Inbox(object):
    """A registered inbox for a given user (provided by Auth0)."""
    def __init__(self, slug):
        self.slug = slug

    @property
    def auth_id(self):
        q = "SELECT * FROM inboxes WHERE slug=:inbox"
        r = db.query(q, inbox=self.slug).all()
        return r[0]['auth_id']


    @classmethod
    def is_linked(cls, auth_id):
        q = 'SELECT * from inboxes where auth_id = :auth_id'
        r = db.query(q, auth_id=auth_id).all()
        return bool(len(r))

    @classmethod
    def store(cls, slug, auth_id):
        q = 'INSERT into inboxes (slug, auth_id) VALUES (:slug, :auth_id)'
        r = db.query(q, slug=slug, auth_id=auth_id)

        return Inbox(slug, body, byline)

    @classmethod
    def does_exist(cls, slug):
        q = 'SELECT * from inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(len(r))

    def submit_note(self, body, byline):
        note = Note.from_inbox(self.slug, body, byline)
        note.store()
        return note

    @property
    def email(self):
        # TODO: Grab the email address from Auth0.
        return auth0.users.get(self.auth_id)['email']

    @property
    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = 'SELECT * from notes where inboxes_auth_id = :auth_id'
        r = db.query(q, auth_id=self.auth_id).all()

        notes = [Note.from_inbox(self.slug, n['body'], n['byline']) for n in r]
        return notes[::-1]

















