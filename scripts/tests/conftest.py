"""
Stub external dependencies so new_post.py can be imported without
installing anthropic, google-auth-oauthlib, or google-api-python-client.
"""
import sys
from unittest.mock import MagicMock

sys.modules["anthropic"] = MagicMock()
sys.modules["google.auth"] = MagicMock()
sys.modules["google.auth.transport"] = MagicMock()
sys.modules["google.auth.transport.requests"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.oauth2.credentials"] = MagicMock()
sys.modules["google_auth_oauthlib"] = MagicMock()
sys.modules["google_auth_oauthlib.flow"] = MagicMock()
sys.modules["googleapiclient"] = MagicMock()
sys.modules["googleapiclient.discovery"] = MagicMock()

# Add the scripts/ directory to the path so test files can import new_post
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
