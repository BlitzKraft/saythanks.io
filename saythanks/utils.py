import re


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
