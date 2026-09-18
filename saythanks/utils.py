import re


def strip_html(text):
    """Remove HTML and CSS tags from a string."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove CSS tags
    pattern = r"\s*[\w\s\.\#,-:]+\s*\{[^}]*\}"
    text = re.sub(pattern, "", text)

    return text


def resolve_nickname(user_detail_info, email, userid):
    """Fall back through nickname -> email local-part -> sanitized name -> user id.

    Not every social connection returns a usable nickname (X's default
    nickname doesn't match the handle; a LinkedIn custom OIDC connection
    doesn't set one at all; Facebook may only provide a full name without
    an email/nickname), so signup must not crash on a missing field.
    """
    nickname = user_detail_info.get('nickname')
    if nickname:
        return nickname

    if email:
        return email.split('@')[0]

    name = user_detail_info.get('name') or user_detail_info.get('given_name')
    if name:
        cleaned_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', name.lower()).strip('-_')
        if cleaned_name:
            return cleaned_name

    return userid
