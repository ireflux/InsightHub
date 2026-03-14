import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.cli import _requires_sources


def test_requires_sources_for_run_and_fetch():
    assert _requires_sources(None) is True
    assert _requires_sources("run") is True
    assert _requires_sources("fetch") is True


def test_requires_sources_is_false_for_non_fetch_commands():
    assert _requires_sources("summarize") is False
    assert _requires_sources("distribute") is False
    assert _requires_sources("debug-summary-input") is False
