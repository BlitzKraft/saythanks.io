import os

import records
import sqlalchemy
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
        self.archived = None

    def __repr__(self):
        return '<Note size={}>'.format(len(self.body))

    @classmethod
    def fetch(cls, uuid):
        """

        :param uuid: 

        """
        self = cls()
        q = "SELECT * FROM notes WHERE uuid=:uuid"
        r = db.query(q, uuid=uuid)

        self.body = r[0]['body']
        self.byline = r[0]['byline']
        self.uuid = uuid

        return self

    @classmethod
    def from_inbox(cls, inbox, body, byline, archived=False, uuid=None):
        """Creates a Note instance from a given inbox.

        :param inbox: 
        :param body: 
        :param byline: 
        :param archived:  (Default value = False)
        :param uuid:  (Default value = None)

        """
        self = cls()

        self.body = body
        self.byline = byline
        self.uuid = uuid
        self.archived = archived
        self.inbox = Inbox(inbox)

        return self

    @classmethod
    def does_exist(cls, uuid):
        """

        :param uuid: 

        """
        q = 'SELECT * from notes where uuid = :uuid'
        try:
            r = db.query(q, uuid=uuid).all()
        # Catch SQL Errors here.
        except sqlalchemy.exc.DataError:
            return False

        return bool(len(r))

    def store(self):
        """Stores the Note instance to the database."""
        q = 'INSERT INTO notes (body, byline, inboxes_auth_id) VALUES (:body, :byline, :inbox)'
        db.query(q, body=self.body, byline=self.byline, inbox=self.inbox.auth_id)

    def archive(self):
        """ """
        q = "UPDATE notes SET archived = 't' WHERE uuid = :uuid"
        db.query(q, uuid=self.uuid)

    def notify(self, email_address):
        """

        :param email_address: 

        """
        email.notify(self, email_address)



class Inbox(object):
    """A registered inbox for a given user (provided by Auth0)."""
    def __init__(self, slug):
        self.slug = slug

    @property
    def auth_id(self):
        """ """
        q = "SELECT * FROM inboxes WHERE slug=:inbox"
        r = db.query(q, inbox=self.slug).all()
        return r[0]['auth_id']


    @classmethod
    def is_linked(cls, auth_id):
        """

        :param auth_id: 

        """
        q = 'SELECT * from inboxes where auth_id = :auth_id'
        r = db.query(q, auth_id=auth_id).all()
        return bool(len(r))

    @classmethod
    def store(cls, slug, auth_id):
        """

        :param slug: 
        :param auth_id: 

        """
        q = 'INSERT into inboxes (slug, auth_id) VALUES (:slug, :auth_id)'
        r = db.query(q, slug=slug, auth_id=auth_id)

        return cls(slug)

    @classmethod
    def does_exist(cls, slug):
        """

        :param slug: 

        """
        q = 'SELECT * from inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(len(r))

    @classmethod
    def is_email_enabled(cls, slug):
        """

        :param slug: 

        """
        q = 'SELECT email_enabled FROM inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(r[0]['email_enabled'])

    @classmethod
    def disable_email(cls, slug):
        """

        :param slug: 

        """
        q = 'update inboxes set email_enabled = false where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def enable_email(cls, slug):
        """

        :param slug: 

        """
        q = 'update inboxes set email_enabled = true where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def is_enabled(cls, slug):
        """

        :param slug: 

        """
        q = 'SELECT enabled FROM inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(r[0]['enabled'])

    @classmethod
    def disable_account(cls, slug):
        """

        :param slug: 

        """
        q = 'update inboxes set enabled = false where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def enable_account(cls, slug):
        """

        :param slug: 

        """
        q = 'update inboxes set enabled = true where slug = :slug'
        r = db.query(q, slug=slug)

    def submit_note(self, body, byline):
        """

        :param body: 
        :param byline: 

        """
        note = Note.from_inbox(self.slug, body, byline)
        note.store()
        return note

    @property
    def email(self):
        """ """
        return auth0.users.get(self.auth_id)['email']

    @property
    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'"
        r = db.query(q, auth_id=self.auth_id).all()

        notes = [Note.from_inbox(self.slug, n['body'], n['byline'], n['archived'], n['uuid']) for n in r]
        return notes[::-1]

    def export(self, format):
        """

        :param format: 

        """
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'"
        r = db.query(q, auth_id=self.auth_id)

        return r.export(format)


    @property
    def archived_notes(self):
        """Returns a list of archived notes, ordered reverse-chronologically."""
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 't'"
        r = db.query(q, auth_id=self.auth_id).all()

        notes = [Note.from_inbox(self.slug, n['body'], n['byline'], n['archived'], n['uuid']) for n in r]
        return notes[::-1]

















