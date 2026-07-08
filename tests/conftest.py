"""Test scaffolding for DB-backed shelter tests.

These tests need a reachable Postgres (see config.yml). If the DB is not
reachable at import time the whole module is skipped, so the pure-logic suite
(test_recurrence_and_errors.py) still runs in isolation.

Requires: pip install pytest
Run:      python -m pytest tests/test_shelter_integration.py
"""
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _db_available():
    try:
        from api import app  # noqa: F401
        from repository import db
        with app.app_context():
            db.session.execute(db.text("SELECT 1"))
        return True
    except Exception:
        return False


db_required = pytest.mark.skipif(not _db_available(), reason="no test database reachable")


@pytest.fixture()
def app_ctx():
    from api import app
    with app.app_context():
        yield app


@pytest.fixture()
def uid():
    return lambda: f"{uuid.uuid4()}"
