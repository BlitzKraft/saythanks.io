# -*- coding: utf-8 -*-

import importlib.util
import os


def _load_utils_module():
    """Import saythanks/utils.py directly, bypassing saythanks/__init__.py.

    The package __init__ imports saythanks.core, which requires optional
    runtime dependencies (mailersend, etc.) and Auth0 environment variables
    that are not available in a plain test environment. utils.py has no
    such dependencies, so it is loaded as a standalone module instead.
    """
    repository_root = os.path.dirname(os.path.dirname(__file__))
    utils_path = os.path.join(repository_root, 'saythanks', 'utils.py')
    spec = importlib.util.spec_from_file_location('saythanks_utils_under_test', utils_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


is_valid_email = _load_utils_module().is_valid_email


def test_valid_emails_pass():
    assert is_valid_email('user@example.com')
    assert is_valid_email('first.last+tag@sub.example.co.uk')


def test_missing_or_empty_email_is_invalid():
    assert not is_valid_email(None)
    assert not is_valid_email('')
    assert not is_valid_email('   ')


def test_malformed_emails_are_invalid():
    assert not is_valid_email('not-an-email')
    assert not is_valid_email('missing-domain@')
    assert not is_valid_email('@missing-local.com')
    assert not is_valid_email('no-at-sign.example.com')
    assert not is_valid_email('has spaces@example.com')
    assert not is_valid_email('no-dot-in-domain@example')


def test_non_string_email_is_invalid():
    assert not is_valid_email(123)
    assert not is_valid_email(['a@b.com'])


def _read_core_source():
    repository_root = os.path.dirname(os.path.dirname(__file__))
    core_path = os.path.join(repository_root, 'saythanks', 'core.py')
    with open(core_path, encoding='utf-8') as core_file:
        return core_file.read()


def test_callback_handling_validates_email_before_db_write():
    """The OAuth callback must reject a malformed (non-empty but invalid)
    email before any downstream user data (nickname resolution, Inbox
    link_or_create) is derived from it and persisted to the database. A
    missing/empty email is allowed through unchanged, since some social
    connections (e.g. Facebook without the email permission) legitimately
    never return one."""
    source = _read_core_source()

    validation_marker = 'if email and not is_valid_email(email):'
    resolve_nickname_call = 'nickname = resolve_nickname(user_detail_info, email, userid)'
    link_or_create_call = 'storage.Inbox.link_or_create(userid, nickname, email)'

    assert validation_marker in source
    assert resolve_nickname_call in source
    assert link_or_create_call in source
    assert source.index(validation_marker) < source.index(resolve_nickname_call)
    assert source.index(validation_marker) < source.index(link_or_create_call)


def test_guard_allows_missing_email_but_blocks_malformed():
    """Mirrors the exact guard condition used in core.callback_handling:
    `if email and not is_valid_email(email): refuse`. A missing/empty email
    must NOT be refused (some auth providers never supply one); a
    non-empty malformed email must be."""
    def would_be_blocked(email):
        return bool(email and not is_valid_email(email))

    # missing / empty email: allowed through (e.g. Facebook auth with no
    # email permission granted)
    assert not would_be_blocked(None)
    assert not would_be_blocked('')

    # malformed non-empty email (including whitespace-only, which is not a
    # legitimate "no email" signal from a provider): blocked
    assert would_be_blocked('   ')
    assert would_be_blocked('not-an-email')
    assert would_be_blocked('missing-domain@')
    assert would_be_blocked('has spaces@example.com')

    # valid email: allowed through
    assert not would_be_blocked('user@example.com')
