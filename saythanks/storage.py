# -*- coding: utf-8 -*-

import records


class Inbox(object):
    """docstring for Inbox"""
    def __init__(self, slug):
        self.slug = slug

    @classmethod
    def is_linked(cls, auth_id):
        q = 'SELECT * from inboxes where auth_id = :auth_id'
        r = records.query(q, auth_id=auth_id)
        return bool(len(r))

    @classmethod
    def store(cls, slug, auth_id):
        q = 'INSERT into inboxes VALUES :slug :auth_id'
        r = records.query(q, slug=slug, auth_id=auth_id)
        return Inbox(slug)

# def add_note(inbox, ):
#     pass