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
    def from_inbox(inbox, body, byline):
        self.body = body
        self.byline = byline
        self.inbox = Inbox(inbox)


class Inbox(object):
    """docstring for Inbox"""
    def __init__(self, slug):
        self.slug = slug


    @classmethod
    def is_linked(cls, auth_id):
        q = 'SELECT * from inboxes where auth_id = :auth_id'
        r = db.query(q, auth_id=auth_id)
        return bool(len(r))

    @classmethod
    def store(cls, slug, auth_id):
        q = 'INSERT into inboxes (slug, auth_id) VALUES (:slug, :auth_id)'
        r = db.query(q, slug=slug, auth_id=auth_id)

        return Inbox(slug)

    def notes(self):
        """Returns a list of notes, ordered reverse-chronologically."""
        q = 'SELECT * from notes where inbox_id = :slug'
        r = db.query(q, slug=self.slug)

        notes = []

        for n in r:
            note = Note.from_inbox(slug, n['body'], n['byline'])

        return notes

