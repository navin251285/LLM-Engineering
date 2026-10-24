"""Shared test setup: the course's llm_replay helper and the app's cassette folder."""
import os
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
COURSE = APP.parent
sys.path.insert(0, str(COURSE))   # llm_replay.py and tut_env.py live in the course folder
os.environ.setdefault("TUT_CASSETTE_DIR", str(APP / "tests" / "cassettes"))
