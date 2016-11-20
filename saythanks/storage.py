# -*- coding: utf-8 -*-

import records


class Inbox(object):
    """docstring for Inbox"""
    def __init__(self, slug)
        self.slug = slug
        self.auth_id = None

    @property
    def auth_id(self):
        pass

    @auth_id.setter
    def auth_id(self, value):
        self.auth_id = value

    def does_exist(self):
        return bool(self.auth_id)

    def create_if_not_stored(self):
        pass

# def add_note(inbox, ):
#     pass