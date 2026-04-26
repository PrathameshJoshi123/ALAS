import base64
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ENCRYPTION_PREFIX = "enc:v1:"
ENVELOPE_ALG = "RSA-OAEP-256+AES-256-GCM"


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8")


def _b64_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def _get_key_material(env_value_name: str, env_path_name: str) -> bytes | None:
    value = os.getenv(env_value_name)
    if value:
        return value.encode("utf-8")

    path_value = os.getenv(env_path_name)
    if path_value:
        key_path = Path(path_value)
        if not key_path.exists():
            raise RuntimeError(f"Configured key file does not exist: {key_path}")
        return key_path.read_bytes()

    return None


@lru_cache(maxsize=1)
def _load_public_key():
    key_bytes = _get_key_material("DATA_RSA_PUBLIC_KEY_PEM", "DATA_RSA_PUBLIC_KEY_PATH")
    if not key_bytes:
        raise RuntimeError(
            "Data encryption key missing. Set DATA_RSA_PUBLIC_KEY_PEM or DATA_RSA_PUBLIC_KEY_PATH."
        )
    return serialization.load_pem_public_key(key_bytes)


@lru_cache(maxsize=1)
def _load_private_key():
    key_bytes = _get_key_material("DATA_RSA_PRIVATE_KEY_PEM", "DATA_RSA_PRIVATE_KEY_PATH")
    if not key_bytes:
        raise RuntimeError(
            "Data decryption key missing. Set DATA_RSA_PRIVATE_KEY_PEM or DATA_RSA_PRIVATE_KEY_PATH."
        )
    return serialization.load_pem_private_key(key_bytes, password=None)


def stable_lookup_hash(value: str) -> str:
    """Create a stable SHA-256 hash for equality lookups over encrypted values."""
    pepper = os.getenv("DATA_ENCRYPTION_PEPPER", "")
    normalized = value.strip().lower()
    return hashlib.sha256(f"{pepper}:{normalized}".encode("utf-8")).hexdigest()


def encrypt_for_storage(value: Any) -> str:
    """
    Encrypt any JSON-serializable value using AES-256-GCM and wrap the AES key
    with RSA-OAEP-SHA256.
    """
    if value is None:
        return value
    if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
        return value

    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, payload, None)

    wrapped_key = _load_public_key().encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    envelope = {
        "v": 1,
        "alg": ENVELOPE_ALG,
        "ek": _b64_encode(wrapped_key),
        "iv": _b64_encode(nonce),
        "ct": _b64_encode(ciphertext),
    }
    encoded_envelope = _b64_encode(
        json.dumps(envelope, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    return f"{ENCRYPTION_PREFIX}{encoded_envelope}"


def decrypt_from_storage(value: Any) -> Any:
    """Decrypt values produced by encrypt_for_storage; pass plaintext through unchanged."""
    if value is None or not isinstance(value, str) or not value.startswith(ENCRYPTION_PREFIX):
        return value

    encoded = value[len(ENCRYPTION_PREFIX) :]
    envelope = json.loads(_b64_decode(encoded).decode("utf-8"))

    encrypted_key = _b64_decode(envelope["ek"])
    nonce = _b64_decode(envelope["iv"])
    ciphertext = _b64_decode(envelope["ct"])

    aes_key = _load_private_key().decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
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
