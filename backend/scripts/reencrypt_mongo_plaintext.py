import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure backend root is on sys.path when running this file directly.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.database import get_db
from services.data_encryption import (
    ENCRYPTION_PREFIX,
    decrypt_from_storage,
    encrypt_for_storage,
    stable_lookup_hash,
)


@dataclass
class MigrationStats:
    scanned: int = 0
    updated: int = 0
    unchanged: int = 0
    errors: int = 0
    error_samples: list[str] | None = None


def _record_error(stats: MigrationStats, collection_name: str, doc_id: Any, exc: Exception) -> None:
    stats.errors += 1
    if stats.error_samples is None:
        stats.error_samples = []
    if len(stats.error_samples) < 5:
        stats.error_samples.append(
            f"{collection_name} _id={doc_id}: {type(exc).__name__}: {str(exc)}"
        )


def validate_encryption_runtime() -> None:
    """Fail fast with a clear message if AES key config is invalid."""
    probe_plaintext = "__migration_probe__"
    encrypted = encrypt_for_storage(probe_plaintext)
    decrypted = decrypt_from_storage(encrypted)
    if decrypted != probe_plaintext:
        raise RuntimeError("Encryption preflight failed: decrypt(encrypt(x)) mismatch")


def is_encrypted(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX)


def should_encrypt(value: Any) -> bool:
    return value is not None and not is_encrypted(value)


def best_effort_plaintext(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and not is_encrypted(value):
        return value
    if is_encrypted(value):
        try:
            decrypted = decrypt_from_storage(value)
            return decrypted if isinstance(decrypted, str) else None
        except Exception:
            return None
    return None


def migrate_collection_fields(
    collection_name: str,
    encrypt_fields: tuple[str, ...],
    dry_run: bool,
) -> MigrationStats:
    db = get_db()
    col = db[collection_name]
    stats = MigrationStats()

    projection = {"_id": 1}
    for field in encrypt_fields:
        projection[field] = 1

    for doc in col.find({}, projection=projection):
        stats.scanned += 1
        set_updates: dict[str, Any] = {}

        try:
            for field in encrypt_fields:
                value = doc.get(field)
                if should_encrypt(value):
                    set_updates[field] = encrypt_for_storage(value)

            if set_updates:
                if not dry_run:
                    col.update_one({"_id": doc["_id"]}, {"$set": set_updates})
                stats.updated += 1
            else:
                stats.unchanged += 1
        except Exception as exc:
            _record_error(stats, collection_name, doc.get("_id"), exc)

    return stats


def migrate_users(dry_run: bool) -> MigrationStats:
    db = get_db()
    col = db.users
    stats = MigrationStats()

    projection = {"_id": 1, "email": 1, "email_hash": 1, "name": 1}
    for doc in col.find({}, projection=projection):
        stats.scanned += 1
        set_updates: dict[str, Any] = {}

        try:
            email_value = doc.get("email")
            name_value = doc.get("name")

            if should_encrypt(email_value):
                normalized = str(email_value).strip().lower()
                set_updates["email"] = encrypt_for_storage(normalized)
                set_updates["email_hash"] = stable_lookup_hash(normalized)
            elif doc.get("email_hash") is None:
                plaintext_email = best_effort_plaintext(email_value)
                if plaintext_email:
                    set_updates["email_hash"] = stable_lookup_hash(plaintext_email.strip().lower())

            if should_encrypt(name_value):
                set_updates["name"] = encrypt_for_storage(name_value)

            if set_updates:
                if not dry_run:
                    col.update_one({"_id": doc["_id"]}, {"$set": set_updates})
                stats.updated += 1
            else:
                stats.unchanged += 1
        except Exception as exc:
            _record_error(stats, "users", doc.get("_id"), exc)

    return stats


def migrate_refresh_tokens(dry_run: bool) -> MigrationStats:
    db = get_db()
    col = db.refresh_tokens
    stats = MigrationStats()

    projection = {"_id": 1, "token": 1, "token_hash": 1}
    for doc in col.find({}, projection=projection):
        stats.scanned += 1
        set_updates: dict[str, Any] = {}

        try:
            token_value = doc.get("token")

            if should_encrypt(token_value):
                token_plain = str(token_value)
                set_updates["token"] = encrypt_for_storage(token_plain)
                set_updates["token_hash"] = stable_lookup_hash(token_plain)
            elif doc.get("token_hash") is None:
                plaintext_token = best_effort_plaintext(token_value)
                if plaintext_token:
                    set_updates["token_hash"] = stable_lookup_hash(plaintext_token)

            if set_updates:
                if not dry_run:
                    col.update_one({"_id": doc["_id"]}, {"$set": set_updates})
                stats.updated += 1
            else:
                stats.unchanged += 1
        except Exception as exc:
            _record_error(stats, "refresh_tokens", doc.get("_id"), exc)

    return stats


def print_stats(name: str, stats: MigrationStats) -> None:
    print(
        f"[{name}] scanned={stats.scanned} updated={stats.updated} "
        f"unchanged={stats.unchanged} errors={stats.errors}"
    )
    if stats.error_samples:
        for sample in stats.error_samples:
            print(f"  ERROR: {sample}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time migration to re-encrypt legacy plaintext Mongo records."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply updates. Without this flag, script runs in dry-run mode.",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"Starting Mongo re-encryption migration in {mode} mode")

    try:
        validate_encryption_runtime()
        print("Encryption preflight check passed")
    except Exception as exc:
        print("Encryption preflight check failed")
        print(f"Reason: {type(exc).__name__}: {str(exc)}")
        print(
            "Set DATA_AES256_KEY_B64 or DATA_AES256_KEY_PATH before running migration."
        )
        sys.exit(1)

    tenants_stats = migrate_collection_fields(
        "tenants",
        ("company_name", "industry", "subscription_tier"),
        dry_run=dry_run,
    )
    users_stats = migrate_users(dry_run=dry_run)
    refresh_stats = migrate_refresh_tokens(dry_run=dry_run)
    contracts_stats = migrate_collection_fields(
        "contracts",
        (
            "company_name",
            "counterparty_name",
            "contract_type",
            "original_filename",
            "analysis_payload",
            "analysis_markdown",
        ),
        dry_run=dry_run,
    )
    qa_stats = migrate_collection_fields(
        "qa_history",
        ("question", "answer"),
        dry_run=dry_run,
    )

    print_stats("tenants", tenants_stats)
    print_stats("users", users_stats)
    print_stats("refresh_tokens", refresh_stats)
    print_stats("contracts", contracts_stats)
    print_stats("qa_history", qa_stats)

    totals = MigrationStats(
        scanned=(
            tenants_stats.scanned
            + users_stats.scanned
            + refresh_stats.scanned
            + contracts_stats.scanned
            + qa_stats.scanned
        ),
        updated=(
            tenants_stats.updated
            + users_stats.updated
            + refresh_stats.updated
            + contracts_stats.updated
            + qa_stats.updated
        ),
        unchanged=(
            tenants_stats.unchanged
            + users_stats.unchanged
            + refresh_stats.unchanged
            + contracts_stats.unchanged
            + qa_stats.unchanged
        ),
        errors=(
            tenants_stats.errors
            + users_stats.errors
            + refresh_stats.errors
            + contracts_stats.errors
            + qa_stats.errors
        ),
    )

    print("-" * 72)
    print_stats("TOTAL", totals)
    if dry_run:
        print("Dry-run complete. Re-run with --apply to persist updates.")
    else:
        print("Migration apply complete.")


if __name__ == "__main__":
    main()
