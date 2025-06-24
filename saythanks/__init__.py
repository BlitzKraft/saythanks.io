from .core import *


@app.context_processor
def inject_version():
    return dict(app_version=app.config.get('APP_VERSION', 'unknown'))
