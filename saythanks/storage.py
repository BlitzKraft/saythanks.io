import logging
from genericpath import exists
import os

import records
import sqlalchemy
from auth0.v2.management import Auth0

from . import myemail
import traceback  # Just to show the full traceback
from psycopg2 import errors

InFailedSqlTransaction = errors.lookup('25P02')
UniqueViolation = errors.lookup('23505')

# importing module

# Create and configure logger
logging.basicConfig(filename='Logfile.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

# Creating an object
logger = logging.getLogger()

# Auth0 API Client
auth0_domain = os.environ['AUTH0_DOMAIN']
auth0_token = os.environ['AUTH0_JWT_V2_TOKEN']
auth0 = Auth0(auth0_domain, auth0_token)

# Database connection.
db = records.Database()

# Storage Models
# Note: Some of these are a little fancy (send email and such).
# --------------


class Note:
    """A generic note of thankfulness."""

    def __init__(self):
        self.body = None
        self.byline = None
        self.inbox = None
        self.archived = None
        self.uuid = None
        self.timestamp = None

    def __repr__(self):
        return '<Note size={}>'.format(len(self.body))

    @classmethod
    def fetch(cls, uuid):
        self = cls()
        q = "SELECT * FROM notes WHERE uuid=:uuid"
        r = db.query(q, uuid=uuid)

        self.body = r[0]['body']
        self.byline = r[0]['byline']
        self.uuid = uuid
        return self

    @classmethod
    def from_inbox(cls, inbox, body, byline, archived=False, uuid=None, timestamp=None):
        """Creates a Note instance from a given inbox."""
        self = cls()

        self.body = body
        self.byline = byline
        self.uuid = uuid
        self.archived = archived
        self.inbox = Inbox(inbox)
        self.timestamp = timestamp
        return self

    @classmethod
    def does_exist(cls, uuid):
        q = 'SELECT * from notes where uuid = :uuid'
        try:
            r = db.query(q, uuid=uuid).all()
        # Catch SQL Errors here.
        except sqlalchemy.exc.DataError:
            logging.error("sqlalchemy.exc.DataError occured")
            return False

        return bool(len(r))

    def store(self):
        """Stores the Note instance to the database."""
        q = 'INSERT INTO notes (body, byline, inboxes_auth_id)' + \
            'VALUES (:body, :byline, :inbox)'
        db.query(q, body=self.body, byline=self.byline,
                 inbox=self.inbox.auth_id)

    def archive(self):
        q = "UPDATE notes SET archived = 't' WHERE uuid = :uuid"
        db.query(q, uuid=self.uuid)

    def notify(self, email_address):
        myemail.notify(self, email_address)


class Inbox:
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
    def store(cls, slug, auth_id, email):
        try:
            q = 'INSERT into inboxes (slug, auth_id,email) VALUES (:slug, :auth_id, :email)'
            r = db.query(q, slug=slug, auth_id=auth_id, email=email)

        except UniqueViolation:
            print('Duplicate record - ID already exist')
            logging.error("ID already exist")
        return cls(slug)

    @classmethod
    def does_exist(cls, slug):
        q = 'SELECT * from inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(len(r))

    @classmethod
    def is_email_enabled(cls, slug):
        q = 'SELECT email_enabled FROM inboxes where slug = :slug'
        try:
            r = db.query(q, slug=slug).all()
            return bool(r[0]['email_enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_email(cls, slug):
        q = 'update inboxes set email_enabled = false where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def enable_email(cls, slug):
        q = 'update inboxes set email_enabled = true where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def is_enabled(cls, slug):
        q = 'SELECT enabled FROM inboxes where slug = :slug'
        try:
            r = db.query(q, slug=slug).all()
            if not r[0]['enabled']:
                return False
            return bool(r[0]['enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_account(cls, slug):
        q = 'update inboxes set enabled = false where slug = :slug'
        r = db.query(q, slug=slug)

    @classmethod
    def enable_account(cls, slug):
        q = 'update inboxes set enabled = true where slug = :slug'
        r = db.query(q, slug=slug)

    def submit_note(self, body, byline):
        note = Note.from_inbox(self.slug, body, byline)
        note.store()
        return note

    @classmethod
    def get_email(cls, slug):
        print(slug, 'email')
        q = 'SELECT email FROM inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return r[0]['email']

    @property
    def myemail(self):
        return auth0.users.get(self.auth_id)['email']
        # emailinfo = auth0.users.get(self.auth_id)['email']
        # print("myemail prop",emailinfo)
        # return emailinfo

    @property
    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'"
        r = db.query(q, auth_id=self.auth_id).all()

        print("all notes", len(r))

        notes = [Note.from_inbox(
            self.slug, n['body'], n['byline'], n['archived'], n['uuid'], n['timestamp']) for n in r]
        return notes[::-1]

    def export(self, file_format):
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'"
        r = db.query(q, auth_id=self.auth_id)
        return r.export(file_format)

    @property
    def archived_notes(self):
        """Returns a list of archived notes, ordered reverse-chronologically."""
        q = "SELECT * from notes where inboxes_auth_id = :auth_id and archived = 't'"
        r = db.query(q, auth_id=self.auth_id).all()

        notes = [Note.from_inbox(
            self.slug, n['body'], n['byline'], n['archived'], n['uuid']) for n in r]
        return notes[::-1]
