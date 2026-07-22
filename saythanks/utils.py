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
