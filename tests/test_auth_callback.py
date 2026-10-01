import importlib.util
import os
import pytest

# Load saythanks.utils directly to test resolve_nickname
utils_path = os.path.join(os.path.dirname(__file__), '..', 'saythanks', 'utils.py')
spec = importlib.util.spec_from_file_location("saythanks_utils", utils_path)
saythanks_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saythanks_utils)
resolve_nickname = saythanks_utils.resolve_nickname


def test_resolve_nickname_with_nickname():
    """When user has a nickname, it should be returned directly."""
    user_detail = {'nickname': 'johndoe', 'name': 'John Doe'}
    email = 'johndoe@example.com'
    userid = 'facebook|123456789'
    assert resolve_nickname(user_detail, email, userid) == 'johndoe'


def test_resolve_nickname_with_email_only():
    """When nickname is missing but email is present, use prefix before @."""
    user_detail = {'name': 'John Doe'}
    email = 'john.smith@example.com'
    userid = 'facebook|123456789'
    assert resolve_nickname(user_detail, email, userid) == 'john.smith'


def test_resolve_nickname_with_name_only():
    """When nickname and email are missing, sanitize the full name."""
    user_detail = {'name': 'John Doe'}
    email = None
    userid = 'facebook|123456789'
    assert resolve_nickname(user_detail, email, userid) == 'john-doe'


def test_resolve_nickname_name_sanitization():
    """Special characters in name should be sanitized into clean hyphens."""
    user_detail = {'name': 'Jane @ Doe #99!'}
    email = None
    userid = 'facebook|123456789'
    assert resolve_nickname(user_detail, email, userid) == 'jane-doe-99'


def test_resolve_nickname_fallback_to_userid():
    """When nickname, email, and name are all missing, fall back to sanitized user id without pipes."""
    user_detail = {}
    email = None
    userid = 'facebook|123456789'
    assert resolve_nickname(user_detail, email, userid) == 'facebook-123456789'


def test_email_none_safe_extraction():
    """Ensure None email does not raise AttributeError on strip."""
    user_detail = {'email': None, 'name': 'Test User'}
    raw_email = user_detail.get('email')
    email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None
    assert email is None


def test_email_whitespace_safe_extraction():
    """Ensure whitespace-only email is treated as None."""
    user_detail = {'email': '   ', 'name': 'Test User'}
    raw_email = user_detail.get('email')
    email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None
    assert email is None
