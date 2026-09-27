import sys
import os

# Add project root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathNormalizer:
    """WSGI middleware to normalize URL paths passed by Vercel serverless routing."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        # Strip /api/index.py or /api/index prefix if added by Vercel rewrites
        if path.startswith("/api/index.py"):
            path = path[len("/api/index.py"):] or "/"
        elif path.startswith("/api/index"):
            path = path[len("/api/index"):] or "/"
        
        # If Vercel provides original path header
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        if matched_path and matched_path != "/api/index" and matched_path != "/api/index.py":
            path = matched_path

        environ["PATH_INFO"] = path
        return self.wsgi_app(environ, start_response)

# Apply middleware to Flask WSGI app
app.wsgi_app = VercelPathNormalizer(app.wsgi_app)
app.debug = False
