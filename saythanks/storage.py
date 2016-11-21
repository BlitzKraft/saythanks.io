# -*- coding: utf-8 -*-

import records

db = records.Database()


class Note(object):
    """A generic note of thankfulness."""
    def __init__(self):
        self.body = None
        self.byline = None
        self.inbox = None

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

    def notify(self):
        # TODO: emails the user when they have received a new note of thanks.
        pass


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

        return Inbox(self.slug, body, byline)

    @classmethod
    def does_exist(cls, slug):
        q = 'SELECT * from inboxes where slug = :slug'
        r = db.query(q, slug=slug).all()
        return bool(len(r))

    def submit_note(self, body, byline):
        return Note.from_inbox(self.slug, body, byline).store()

    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = 'SELECT * from notes where inbox_id = :slug'
        r = db.query(q, slug=self.slug)

        notes = []

        for n in r:
            note = Note.from_inbox(slug, n['body'], n['byline'])

        return notes

