from .core import *


@app.context_processor
def inject_version():
    """Provide the application version to Jinja templates.

    This Flask context processor returns a dict with the key `app_version`
    so templates can reference the current application version as
    `{{ app_version }}`.

    The value is pulled from app.config['APP_VERSION'] if present; otherwise
    the string 'unknown' is returned.

    Example usage in a template:
        <footer>Version: {{ app_version }}</footer>
    """
    return dict(app_version=app.config.get('APP_VERSION', 'unknown'))
