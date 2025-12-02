import pytest
import tempfile
import os
from datetime import datetime

from src.models.transaction import Transaction
from src.database.sqlite_db import SQLiteDB
from src.database.manager import DatabaseManager


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def sqlite_db(temp_db_path):
    """Create a SQLite database instance."""
    db = SQLiteDB(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def db_manager(sqlite_db):
    """Create a database manager with SQLite only."""
    return DatabaseManager(sqlite_db, tidb_db=None)


@pytest.fixture
def sample_transaction():
    """Create a sample transaction."""
    return Transaction(
        user_id=123456,
        type="expense",
        amount=50000,
        category="makanan",
        description="beli makan siang",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_income():
    """Create a sample income transaction."""
    return Transaction(
        user_id=123456,
        type="income",
        amount=5000000,
        category="gaji",
        description="gaji bulanan",
        created_at=datetime.now(),
    )
