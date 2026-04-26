from typing import Any
from bson import ObjectId
from fastapi import Header, HTTPException
from models.database import get_db
from services.data_encryption import decrypt_from_storage
from services.security import decode_token


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = _bearer_token(authorization)

    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token subject missing")

    db = get_db()
    try:
        user_oid = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token subject") from exc

    user = db.users.find_one({"_id": user_oid, "is_active": True})
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    user["email"] = decrypt_from_storage(user.get("email"))
    user["name"] = decrypt_from_storage(user.get("name"))

    user["id"] = str(user["_id"])
    user.pop("_id", None)
    user.pop("password_hash", None)
    return user
