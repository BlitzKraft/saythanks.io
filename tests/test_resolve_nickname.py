# -*- coding: utf-8 -*-
"""Tests for issue #288: callback nickname fallback.

Not every social connection returns a usable `nickname` field (X's default
doesn't match the actual handle; a LinkedIn custom OIDC connection doesn't
set one at all), so `/callback` must not crash when it's missing.
"""

from saythanks.utils import resolve_nickname


def test_uses_nickname_when_present():
    assert resolve_nickname({'nickname': 'octocat'}, 'octocat@example.com', 'auth0|123') == 'octocat'


def test_falls_back_to_email_local_part_when_nickname_missing():
    assert resolve_nickname({}, 'jane.doe@example.com', 'auth0|123') == 'jane.doe'


def test_falls_back_to_user_id_when_nickname_and_email_missing():
    assert resolve_nickname({}, None, 'auth0|123') == 'auth0|123'


def test_empty_string_nickname_is_treated_as_missing():
    assert resolve_nickname({'nickname': ''}, 'jane.doe@example.com', 'auth0|123') == 'jane.doe'


def test_empty_string_email_is_treated_as_missing():
    assert resolve_nickname({}, '', 'auth0|123') == 'auth0|123'
