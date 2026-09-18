# -*- coding: utf-8 -*-
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))


def _load_utils():
    spec = importlib.util.spec_from_file_location(
        'saythanks.utils', os.path.join(ROOT, 'saythanks', 'utils.py')
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules['saythanks.utils'] = mod
    spec.loader.exec_module(mod)
    return mod


utils = _load_utils()
resolve_nickname = utils.resolve_nickname


def test_resolve_nickname_with_nickname_present():
    user_detail_info = {
        'nickname': 'octocat',
        'name': 'Monalisa Octocat',
        'email': 'octocat@github.com'
    }
    result = resolve_nickname(user_detail_info, 'octocat@github.com', 'github|12345')
    assert result == 'octocat'


def test_resolve_nickname_with_missing_nickname_fallback_to_email():
    user_detail_info = {
        'name': 'Jane Doe',
        'email': 'janedoe@example.com'
    }
    result = resolve_nickname(user_detail_info, 'janedoe@example.com', 'auth0|12345')
    assert result == 'janedoe'


def test_resolve_nickname_facebook_profile_with_name_no_email_no_nickname():
    # Common Facebook profile scenario (no email, no nickname, only full name)
    user_detail_info = {
        'name': 'John Doe',
        'picture': 'https://facebook.com/picture.jpg'
    }
    result = resolve_nickname(user_detail_info, None, 'facebook|987654321')
    assert result == 'john-doe'


def test_resolve_nickname_facebook_profile_with_special_characters_in_name():
    user_detail_info = {
        'name': 'John Doe (Software Eng!)',
    }
    result = resolve_nickname(user_detail_info, None, 'facebook|987654321')
    assert result == 'john-doe-software-eng'


def test_resolve_nickname_fallback_to_given_name():
    user_detail_info = {
        'given_name': 'Alice',
    }
    result = resolve_nickname(user_detail_info, None, 'facebook|11111')
    assert result == 'alice'


def test_resolve_nickname_fallback_to_userid_when_all_empty():
    user_detail_info = {}
    result = resolve_nickname(user_detail_info, None, 'auth0|99999')
    assert result == 'auth0|99999'


def test_email_sanitization_logic():
    # Test normalization logic used in core.py
    def normalize_email(user_detail_info):
        raw_email = user_detail_info.get('email')
        return raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

    # When email is missing (None)
    assert normalize_email({}) is None
    assert normalize_email({'email': None}) is None

    # When email is empty string or pure whitespace
    assert normalize_email({'email': ''}) is None
    assert normalize_email({'email': '   \t\n '}) is None

    # When email is non-string (e.g. invalid type)
    assert normalize_email({'email': 12345}) is None
    assert normalize_email({'email': []}) is None

    # When email is valid with surrounding whitespace
    assert normalize_email({'email': '  user@facebook.com  '}) == 'user@facebook.com'
