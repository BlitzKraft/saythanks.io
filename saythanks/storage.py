# -*- coding: utf-8 -*-

import records

db = records.Database()


class Note(object):
    """docstring for Note"""
    def __init__(self):
        self.body = None
        self.byline = None
        self.inbox = None

    @classmethod
    def from_inbox(cls, inbox, body, byline):
        self.body = body
        self.byline = byline
        self.inbox = Inbox(inbox)

    def store():
        q = 'INERT into notes (body, byline) (:body, :byline)'
        r = db.query(q, body=self.body, byline=self.byline).all()
        return bool(len(r))


class Inbox(object):
    """docstring for Inbox"""
    def __init__(self, slug):
        self.slug = slug


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

    def submit_note(self, body, byline):
        return Note.from_inbox().store()

    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = 'SELECT * from notes where inbox_id = :slug'
        r = db.query(q, slug=self.slug)

        notes = []

        for n in r:
            note = Note.from_inbox(slug, n['body'], n['byline'])

        return notes

