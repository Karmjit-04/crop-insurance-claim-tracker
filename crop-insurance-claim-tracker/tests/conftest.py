"""Adds the app/ folder to sys.path so tests can import `agent` and `database`."""

import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
