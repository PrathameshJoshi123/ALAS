from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from models.database import get_db, now_utc
from services.data_encryption import decrypt_from_storage, encrypt_for_storage, stable_lookup_hash
from services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class CreateTenantRequest(BaseModel):
    company_name: str = Field(min_length=2)
    industry: str = "general"
    subscription_tier: str = "starter"


class SignupRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _serialize_tenant(doc: dict) -> dict:
    company_name = decrypt_from_storage(doc.get("company_name", doc.get("company_name_enc")))
    industry = decrypt_from_storage(doc.get("industry", doc.get("industry_enc")))
    subscription_tier = decrypt_from_storage(doc.get("subscription_tier", doc.get("subscription_tier_enc")))
    return {
        "id": str(doc["_id"]),
        "company_name": company_name,
        "industry": industry,
        "subscription_tier": subscription_tier,
        "created_at": doc.get("created_at"),
    }


def _serialize_user(doc: dict) -> dict:
    email = decrypt_from_storage(doc.get("email", doc.get("email_enc")))
    name = decrypt_from_storage(doc.get("name", doc.get("name_enc")))
    return {
        "id": str(doc["_id"]),
        "tenant_id": doc.get("tenant_id"),
        "email": email,
        "name": name,
        "role_id": doc.get("role_id", "member"),
        "is_active": doc.get("is_active", True),
        "email_verified": doc.get("email_verified", True),
    }


@router.post("/tenants")
def create_tenant(payload: CreateTenantRequest):
    db = get_db()
    now = now_utc()

    tenant_doc = {
        "company_name": encrypt_for_storage(payload.company_name.strip()),
        "industry": encrypt_for_storage(payload.industry.strip()),
        "subscription_tier": encrypt_for_storage(payload.subscription_tier.strip()),
        "created_at": now,
        "updated_at": now,
    }

    inserted = db.tenants.insert_one(tenant_doc)
    tenant_doc["_id"] = inserted.inserted_id
    return _serialize_tenant(tenant_doc)


@router.get("/tenants")
def list_tenants():
    db = get_db()
    tenants = db.tenants.find().sort("created_at", -1)
    return [_serialize_tenant(t) for t in tenants]


@router.post("/signup")
def signup(payload: SignupRequest):
    db = get_db()
    normalized_email = payload.email.lower().strip()
    email_hash = stable_lookup_hash(normalized_email)

    try:
        tenant_oid = ObjectId(payload.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid tenant_id") from exc

    tenant = db.tenants.find_one({"_id": tenant_oid})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    existing = db.users.find_one(
        {
            "tenant_id": payload.tenant_id,
            "email_hash": email_hash,
        }
    )
    if not existing:
        existing = db.users.find_one(
            {
                "tenant_id": payload.tenant_id,
                "email": normalized_email,
            }
        )
    if existing:
        raise HTTPException(status_code=409, detail="User already exists for this tenant")

    now = now_utc()
    user_doc = {
        "tenant_id": payload.tenant_id,
        "email": encrypt_for_storage(normalized_email),
        "email_hash": email_hash,
        "password_hash": hash_password(payload.password),
        "name": encrypt_for_storage(payload.name.strip()),
        "role_id": "member",
        "is_active": True,
        "email_verified": True,
        "created_at": now,
        "updated_at": now,
    }

    inserted = db.users.insert_one(user_doc)
    user_doc["_id"] = inserted.inserted_id
    return _serialize_user(user_doc)


@router.post("/login")
def login(payload: LoginRequest):
    db = get_db()
    normalized_email = payload.email.lower().strip()
    email_hash = stable_lookup_hash(normalized_email)

    user = db.users.find_one(
        {
            "tenant_id": payload.tenant_id,
            "email_hash": email_hash,
            "is_active": True,
        }
    )
    if not user:
        user = db.users.find_one(
            {
                "tenant_id": payload.tenant_id,
                "email": normalized_email,
                "is_active": True,
            }
        )
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = str(user["_id"])
    user_email = decrypt_from_storage(user.get("email", user.get("email_enc")))
    access_token = create_access_token(user_id, payload.tenant_id, user_email)
    refresh_token, refresh_expires_at = create_refresh_token(user_id, payload.tenant_id, user_email)

    db.refresh_tokens.insert_one(
        {
            "token": encrypt_for_storage(refresh_token),
            "token_hash": stable_lookup_hash(refresh_token),
            "user_id": user_id,
            "tenant_id": payload.tenant_id,
            "expires_at": refresh_expires_at,
            "revoked": False,
            "created_at": now_utc(),
        }
    )

    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "last_login_at": now_utc(),
                "updated_at": now_utc(),
            }
        },
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _serialize_user(user),
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest):
    db = get_db()

    token_hash = stable_lookup_hash(payload.refresh_token)
    token_doc = db.refresh_tokens.find_one({"token_hash": token_hash, "revoked": False})
    if not token_doc:
        token_doc = db.refresh_tokens.find_one({"token": payload.refresh_token, "revoked": False})
    if not token_doc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_doc.get("expires_at") and token_doc["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = token_payload.get("sub")
    tenant_id = token_payload.get("tenant_id")
    email = token_payload.get("email")

    user = db.users.find_one({"_id": ObjectId(user_id), "is_active": True})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(user_id, tenant_id, email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(user_id: str, tenant_id: str):
    db = get_db()
    db.refresh_tokens.update_many(
        {"user_id": user_id, "tenant_id": tenant_id, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": now_utc()}},
    )
    return {"success": True}


@router.get("/users/{user_id}")
def get_user(user_id: str):
    db = get_db()

    try:
        user_oid = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = db.users.find_one({"_id": user_oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _serialize_user(user)
