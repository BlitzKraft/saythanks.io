from .core import *

# Import your get_version function
from .version import get_version

@app.context_processor
def inject_version():
    return dict(app_version=get_version())