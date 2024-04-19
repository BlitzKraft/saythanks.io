import logging
import os
from kinde_sdk.kinde_api_client import GrantType, KindeApiClient
from kinde_sdk import Configuration
import tablib
import sqlalchemy
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

# Database connection.
engine = sqlalchemy.create_engine(os.environ['DATABASE_URL'])
conn = engine.connect()

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
        q = sqlalchemy.text("SELECT * FROM notes WHERE uuid=:uuid")
        r = conn.execute(q,{'uuid': uuid}).fetchall()
        r=[dict(i._mapping) for i in r]
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
        q = sqlalchemy.text('SELECT * from notes where uuid = :uuid')
        r = conn.execute(q,{'uuid': uuid}).fetchall()
        r=[dict(i._mapping) for i in r]
        return bool(len(r))

    def store(self):
        """Stores the Note instance to the database."""
        q = 'INSERT INTO notes (body, byline, inboxes_auth_id)' + \
            'VALUES (:body, :byline, :inbox)'
        q = sqlalchemy.text(q)
        conn.execute(q, {'body': self.body, 'byline': self.byline, 'inbox': self.inbox.auth_id})

    def archive(self):
        q = sqlalchemy.text("UPDATE notes SET archived = 't' WHERE uuid = :uuid")
        conn.execute(q, {'uuid': self.uuid})

    def notify(self, email_address):
        myemail.notify(self, email_address)


class Inbox:
    """A registered inbox for a given user (provided by Auth0)."""

    def __init__(self, slug):
        self.slug = slug

    @property
    def auth_id(self):
        q = sqlalchemy.text("SELECT * FROM inboxes WHERE slug=:slug")
        r = conn.execute(q, {'slug': self.slug}).fetchall()
        r=[dict(i._mapping) for i in r]
        return r[0]['auth_id']

    @classmethod
    def is_linked(cls, auth_id):
        q = sqlalchemy.text('SELECT * from inboxes where auth_id = :auth_id')
        r = conn.execute(q, {'auth_id': auth_id}).fetchall()
        r=[dict(i._mapping) for i in r]
        return bool(len(r))

    @classmethod
    def store(cls, slug, auth_id, email):
        try:
            q = sqlalchemy.text('INSERT into inboxes (slug, auth_id, email) VALUES (:slug, :auth_id, :email)')
            conn.execute(q, {'slug': slug, 'auth_id': auth_id, 'email': email})

        except UniqueViolation:
            print('Duplicate record - ID already exists')
            logging.error("ID already exists")
        return cls(slug)

    @classmethod
    def does_exist(cls, slug):
        q = sqlalchemy.text('SELECT * from inboxes where slug = :slug')
        r = conn.execute(q, {'slug': slug}).fetchall()
        r=[dict(i._mapping) for i in r]
        return bool(len(r))

    @classmethod
    def is_email_enabled(cls, slug):
        q = sqlalchemy.text('SELECT email_enabled FROM inboxes where slug = :slug')
        try:
            r = conn.execute(q, {'slug': slug}).fetchall()
            r=[dict(i._mapping) for i in r]
            return bool(r[0]['email_enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_email(cls, slug):
        q = sqlalchemy.text('update inboxes set email_enabled = false where slug = :slug')
        conn.execute(q, {'slug': slug})

    @classmethod
    def enable_email(cls, slug):
        q = sqlalchemy.text('update inboxes set email_enabled = true where slug = :slug')
        conn.execute(q, {'slug': slug})

    @classmethod
    def is_enabled(cls, slug):
        q = sqlalchemy.text('SELECT enabled FROM inboxes where slug = :slug')
        try:
            r = conn.execute(q, {'slug': slug}).fetchall()
            r=[dict(i._mapping) for i in r]
            if not r[0]['enabled']:
                return False
            return bool(r[0]['enabled'])
        except InFailedSqlTransaction:
            print(traceback.print_exc())
            logging.error(traceback.print_exc())
            return False

    @classmethod
    def disable_account(cls, slug):
        q = sqlalchemy.text('update inboxes set enabled = false where slug = :slug')
        conn.execute(q, {'slug': slug})

    @classmethod
    def enable_account(cls, slug):
        q = sqlalchemy.text('update inboxes set enabled = true where slug = :slug')
        conn.execute(q, {'slug': slug})

    def submit_note(self, body, byline):
        note = Note.from_inbox(self.slug, body, byline)
        note.store()
        return note

    @classmethod
    def get_email(cls, slug):
        q = sqlalchemy.text('SELECT email FROM inboxes where slug = :slug')
        r = conn.execute(q, {'slug': slug}).fetchall()
        r=[dict(i._mapping) for i in r]
        return r[0]['email']

    @property
    def myemail(self):
        return kinde_client.get_user_details()['email']
        # emailinfo = auth0.users.get(self.auth_id)['email']
        # print("myemail prop",emailinfo)
        # return emailinfo

    @property
    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = sqlalchemy.text("SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'")
        r = conn.execute(q, {'auth_id': self.auth_id}).fetchall()
        r=[dict(i._mapping) for i in r]

        notes = [
            Note.from_inbox(
                self.slug,
                n["body"], n["byline"], n["archived"], n["uuid"], n["timestamp"]
            )
            for n in r
        ]
        return notes[::-1]
    
    def search_notes(self, search_str):
        """Returns a list of notes, queried by search string "param" """
        q = sqlalchemy.text("""SELECT * from notes where ( body LIKE '%' || :param || '%' or byline LIKE '%' || :param || '%' ) and inboxes_auth_id = :auth_id""")
        r = conn.execute(q, {'param': search_str, 'auth_id': self.auth_id}).fetchall()
        r=[dict(i._mapping) for i in r]

        notes = [
            Note.from_inbox(
                self.slug,
                n["body"], n["byline"], n["archived"], n["uuid"], n["timestamp"]
            )
            for n in r
        ]
        return notes[::-1]

    def export(self, file_format):
        q = sqlalchemy.text("SELECT * from notes where inboxes_auth_id = :auth_id and archived = 'f'")
        r = conn.execute(q, {'auth_id': self.auth_id}).fetchall()
        r=[dict(i._mapping) for i in r]
        return tablib.Dataset(r).export(file_format)

    @property
    def archived_notes(self):
        """Returns a list of archived notes, ordered reverse-chronologically."""
        q = sqlalchemy.text("SELECT * from notes where inboxes_auth_id = :auth_id and archived = 't'")
        r = conn.execute(q, {'auth_id': self.auth_id}).fetchall()
        r=[dict(i._mapping) for i in r]

        notes = [Note.from_inbox(
            self.slug, n['body'], n['byline'], n['archived'], n['uuid']) for n in r]
        return notes[::-1]
