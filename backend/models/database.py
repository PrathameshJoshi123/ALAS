import os
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "alas")

_client = None
_db = None


def get_db():
    """Return a singleton Mongo database handle."""
    global _client, _db

    if _db is not None:
        return _db

    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not configured")

    _client = MongoClient(MONGO_URI)
    _db = _client[MONGO_DB_NAME]
    return _db


def now_utc():
    return datetime.now(timezone.utc)


def init_db_indexes() -> None:
    """Create collections/indexes needed by auth + contract flows."""
    db = get_db()

    db.tenants.create_index([("company_name", ASCENDING)])

    db.users.create_index(
        [("tenant_id", ASCENDING), ("email", ASCENDING)],
        unique=True,
        name="uniq_user_per_tenant",
    )
    db.users.create_index([("tenant_id", ASCENDING)])

    db.refresh_tokens.create_index([("token", ASCENDING)], unique=True)
    db.refresh_tokens.create_index([("user_id", ASCENDING)])
    db.refresh_tokens.create_index([("expires_at", ASCENDING)])

    db.contracts.create_index([("owner_user_id", ASCENDING), ("created_at", DESCENDING)])
    db.contracts.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])
    db.contracts.create_index([("markdown_file", ASCENDING)])

    db.qa_history.create_index([("contract_id", ASCENDING), ("created_at", DESCENDING)])
    db.qa_history.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
