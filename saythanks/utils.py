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
    """Fall back through nickname -> email local-part -> sanitized name -> sanitized userid.

    Not every social connection returns a usable nickname (e.g. Facebook
    when users don't share email, or custom OIDC connections), so signup must
    not crash on a missing field and must always produce a clean, URL-safe slug.
    """
    nickname = user_detail_info.get('nickname')
    if nickname and isinstance(nickname, str) and nickname.strip():
        return nickname.strip()

    if email and isinstance(email, str) and email.strip():
        local_part = email.strip().split('@')[0]
        if local_part:
            return local_part

    name = user_detail_info.get('name') or user_detail_info.get('given_name')
    if name and isinstance(name, str):
        cleaned_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', name.lower()).strip('-_')
        if cleaned_name:
            return cleaned_name

    if userid and isinstance(userid, str):
        cleaned_uid = re.sub(r'[^a-zA-Z0-9_-]+', '-', userid.lower()).strip('-_')
        if cleaned_uid:
            return cleaned_uid

    return userid
