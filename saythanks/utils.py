import re


def strip_html(text):
    if not text:
        return ""
    # Remove HTML tags
    return re.sub(r'<[^>]+>', '', text)
