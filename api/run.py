import os
import sys

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.dashboard.app import app


class RunEndpointWrapper:
    """
    WSGI wrapper ensuring any request hitting api/run.py executes /api/run.
    Handles differences in Vercel's PATH_INFO passing (/ vs /api/run).
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        environ["PATH_INFO"] = "/api/run"
        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI application for /api/run
app.wsgi_app = RunEndpointWrapper(app.wsgi_app)
