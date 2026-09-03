import re


# RFC 5322-inspired but intentionally conservative: local-part and domain
# separated by a single '@', domain has at least one '.', no whitespace.
EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def is_valid_email(email):
    """Return True if `email` looks like a syntactically valid address.

    Used to gate any user-info write to the database on OAuth callback,
    since identity providers are not guaranteed to return a usable email
    (missing, empty, or malformed depending on the social connection).
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_RE.match(email.strip()))


def strip_html(text):
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove CSS tags
    pattern = r"\s*[\w\s\.\#,-:]+\s*\{[^}]*\}"
    text = re.sub(pattern, "", text)

    return text


def resolve_nickname(user_detail_info, email, userid):
    """Fall back through nickname -> email local-part -> user id.

    Not every social connection returns a usable nickname (X's default
    nickname doesn't match the handle; a LinkedIn custom OIDC connection
    doesn't set one at all), so signup must not crash on a missing field.
    """
    return (
        user_detail_info.get('nickname')
        or (email.split('@')[0] if email else None)
        or userid
    )
