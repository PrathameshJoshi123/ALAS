import base64
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ENCRYPTION_PREFIX = "enc:"
ENCRYPTION_PREFIX_V2 = "enc:v2:"
ENVELOPE_ALG = "AES-256-GCM"


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8")


def _b64_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def _get_key_material(env_value_name: str, env_path_name: str) -> str | None:
    value = os.getenv(env_value_name)
    if value:
        return value.strip()

    path_value = os.getenv(env_path_name)
    if path_value:
        key_path = Path(path_value)
        if not key_path.exists():
            raise RuntimeError(f"Configured key file does not exist: {key_path}")
        return key_path.read_text(encoding="utf-8").strip()

    return None


@lru_cache(maxsize=1)
def _load_aes256_key() -> bytes:
    key_b64 = _get_key_material("DATA_AES256_KEY_B64", "DATA_AES256_KEY_PATH")
    if not key_b64:
        raise RuntimeError(
            "Data encryption key missing. Set DATA_AES256_KEY_B64 or DATA_AES256_KEY_PATH."
        )
    try:
        key = _b64_decode(key_b64)
    except Exception as exc:
        raise RuntimeError("Invalid DATA_AES256_KEY_B64 format. Must be base64-encoded bytes.") from exc
    if len(key) != 32:
        raise RuntimeError(
            f"Invalid AES key length: expected 32 bytes for AES-256, got {len(key)} bytes."
        )
    return key


def stable_lookup_hash(value: str) -> str:
    """Create a stable SHA-256 hash for equality lookups over encrypted values."""
    pepper = os.getenv("DATA_ENCRYPTION_PEPPER", "")
    normalized = value.strip().lower()
    return hashlib.sha256(f"{pepper}:{normalized}".encode("utf-8")).hexdigest()


def encrypt_for_storage(value: Any) -> str:
    """
    Encrypt any JSON-serializable value using AES-256-GCM.
    """
    if value is None:
        return value
    if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
        return value

    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    aes_key = _load_aes256_key()
    nonce = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, payload, None)

    envelope = {
        "v": 2,
        "alg": ENVELOPE_ALG,
        "iv": _b64_encode(nonce),
        "ct": _b64_encode(ciphertext),
    }
    encoded_envelope = _b64_encode(
        json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    return f"{ENCRYPTION_PREFIX_V2}{encoded_envelope}"


def decrypt_from_storage(value: Any) -> Any:
    """Decrypt values produced by encrypt_for_storage; pass plaintext through unchanged."""
    if value is None or not isinstance(value, str) or not value.startswith(ENCRYPTION_PREFIX):
        return value

    if not value.startswith(ENCRYPTION_PREFIX_V2):
        raise RuntimeError("Unsupported encrypted payload version. Re-encrypt data using AES-256.")

    encoded = value[len(ENCRYPTION_PREFIX_V2) :]
    envelope = json.loads(_b64_decode(encoded).decode("utf-8"))

    nonce = _b64_decode(envelope["iv"])
    ciphertext = _b64_decode(envelope["ct"])

    aes_key = _load_aes256_key()
    decrypted = AESGCM(aes_key).decrypt(nonce, ciphertext, None)
    return json.loads(decrypted.decode("utf-8"))


def encrypt_fields(doc: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    result = dict(doc)
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = encrypt_for_storage(result[field])
    return result


def decrypt_fields(doc: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    result = dict(doc)
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = decrypt_from_storage(result[field])
    return result
