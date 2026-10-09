import os
import sys

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.dashboard.app import app


class VercelWSGIWrapper:
    """Normalizes PATH_INFO when invoked inside Vercel Serverless environment."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith("/api/index.py"):
            environ["PATH_INFO"] = path[len("/api/index.py"):] or "/"
        elif path.startswith("/api/index"):
            environ["PATH_INFO"] = path[len("/api/index"):] or "/"
        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI callable for Vercel
app.wsgi_app = VercelWSGIWrapper(app.wsgi_app)
