# TE Legal Platform - Backend Architecture

A secure, multi-tenant legal technology platform with AI-assisted contract and compliance management.

## Architecture Overview

### Project Structure

```
backend/
├── services/
│   ├── auth/                    # Authentication & Authorization Service
│   │   ├── routes/             # API endpoints
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── models/             # Auth-specific models (future)
│   │   └── utils/              # Business logic & helpers
│   ├── (future services)
│
├── shared/                      # Shared utilities across all services
│   ├── database/               # Database connection & ORM models
│   ├── encryption/             # AES-256 encryption for PII (DPDP compliant)
│   ├── jwt_handler/            # JWT token generation & validation
│   ├── redis_client/           # Redis client for sessions & caching
│   └── audit/                  # Audit logging for compliance
│
├── config/                      # Configuration & settings
├── alembic/                     # Database migrations
├── main.py                      # FastAPI application entry point
└── requirements.txt             # Python dependencies
```

## Key Architecture Decisions

### 1. Multi-Tenancy Model

- **Single Database**: All tenants share one PostgreSQL database
- **Tenant Isolation**: Via `tenant_id` filtering in queries (application-level for now)
- **Future RLS**: Row-Level Security can be added to enforce isolation at database level

### 2. Encryption Strategy (DPDP Act Compliance)

- **Email**: Encrypted + Hashed for searchable lookups
  - `email_encrypted`: AES-256 encrypted email
  - `email_hash`: HMAC-SHA256 hash for unique identification
- **Name**: AES-256 encrypted (not searchable)
- **Passwords**: Bcrypt hashed (never encrypted)

**Why both encryption and hash?**

- Encryption protects data at rest (DPDP requirement)
- Hash allows login verification without decryption

### 3. Token Management

- **Access Tokens**: Short-lived (15 min), contains permissions
- **Refresh Tokens**: Long-lived (7 days), stored in Redis for revocation
- **Permissions Caching**: Role permissions cached in Redis with 1-hour TTL

### 4. Default Roles & Permissions

Five default roles created at tenant onboarding:

1. **Junior Associate**: Read contracts, create drafts, submit for review
2. **Senior Associate**: Review & approve, broader access to compliance
3. **Compliance Officer**: Manage filings, deadlines, compliance status
4. **In-House Counsel**: Full contract management, strategic decisions
5. **Senior Partner**: System admin + all permissions

Each role has a `permission_matrix` (JSON) defining access to:

- Contracts (view, create, review, approve, execute)
- Compliance (view, manage, generate reports)
- Employment (documents, reviews, decisions)
- Admin (user/role management, audit logs)

### 5. Audit Logging

Every auth event is logged:

- Event type (login, logout, signup, refresh, role_created, etc.)
- Status (success/failure)
- User & tenant
- IP address, user agent
- Timestamp

Accessible to: Tenant admin + super admin

## Security Features

### Encryption

- **Algorithm**: AES-256-CBC (256-bit keys)
- **Padding**: PKCS7
- **IV**: Random per encryption (prevents pattern analysis)
- **Key Storage**: Environment variables (base64 encoded)

### Authentication

- **Passwords**: Bcrypt with 12 rounds
- **JWT**: HS256 HMAC-based signatures
- **Refresh Token Revocation**: Via Redis

### Data Isolation

- Every query filtered by `tenant_id`
- Users can only access their tenant's data
- Audit logs maintained separately

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### 1. Environment Setup

```bash
cd backend

# Copy example to actual .env
cp .env.example .env

# Generate proper encryption keys
# Option A: Python
python -c "
import os
from base64 import b64encode
from cryptography.hazmat.primitives.ciphers import algorithms

# Generate 256-bit key
key = os.urandom(32)
iv = os.urandom(16)

print(f'AES_KEY={b64encode(key).decode()}')
print(f'AES_IV={b64encode(iv).decode()}')
"

# Option B: OpenSSL
openssl enc -aes-256-cbc -P -S 1234567890123456 -pass pass:mypassword -nosalt | head -1
```

Update `.env` with:

- `DATABASE_URL`: Your PostgreSQL connection string
- `REDIS_HOST`, `REDIS_PORT`: Your Redis server
- `SECRET_KEY`: Min 32 characters for JWT signing
- `AES_KEY`, `AES_IV`: Generated above

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database initialization

```bash
# Run migrations
alembic upgrade head

# Or create tables directly (for development)
python -c "from shared.database.db import init_db; init_db()"
```

### 4. Run the Application

```bash
# Development
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

Application will be available at: `http://localhost:8000`

## API Endpoints

### Authentication

#### Create Tenant

```http
POST /api/auth/tenants
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "industry": "Technology",
  "subscription_tier": "pro"
}
```

#### Sign Up

```http
POST /api/auth/signup
Content-Type: application/json

{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "John Doe"
}
```

#### Log In

```http
POST /api/auth/login
Content-Type: application/json

{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "tenant_id": "...",
    "email": "user@example.com",
    "name": "John Doe",
    "role_id": "...",
    "is_active": true,
    "email_verified": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

#### Refresh Token

```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Log Out

```http
POST /api/auth/logout?user_id=...&tenant_id=...
```

## Database Schema

### Tenants Table

| Column            | Type         | Description             |
| ----------------- | ------------ | ----------------------- |
| id                | UUID         | Primary key             |
| company_name      | VARCHAR(255) | Legal company name      |
| industry          | VARCHAR(100) | Industry classification |
| subscription_tier | ENUM         | free, pro, enterprise   |
| created_at        | TIMESTAMP    | Creation time           |
| updated_at        | TIMESTAMP    | Last update             |
| version           | INTEGER      | Optimistic locking      |

### Roles Table

| Column            | Type         | Description                  |
| ----------------- | ------------ | ---------------------------- |
| id                | UUID         | Primary key                  |
| tenant_id         | UUID         | Foreign key to tenants       |
| role_name         | VARCHAR(100) | Role identifier              |
| permission_matrix | JSON         | JSONB permission definitions |
| created_at        | TIMESTAMP    | Creation time                |
| updated_at        | TIMESTAMP    | Last update                  |
| version           | INTEGER      | Optimistic locking           |

### Users Table

| Column          | Type         | Description                    |
| --------------- | ------------ | ------------------------------ |
| id              | UUID         | Primary key                    |
| tenant_id       | UUID         | Foreign key to tenants (RLS)   |
| name_encrypted  | TEXT         | AES-256 encrypted name         |
| email_encrypted | TEXT         | AES-256 encrypted email        |
| email_hash      | VARCHAR(255) | HMAC-SHA256 hash for lookups   |
| password_hash   | VARCHAR(255) | Bcrypt hash                    |
| role_id         | UUID         | Foreign key to roles           |
| is_active       | INTEGER      | 1 = active, 0 = inactive       |
| email_verified  | INTEGER      | 1 = verified, 0 = not verified |
| created_at      | TIMESTAMP    | Creation time                  |
| updated_at      | TIMESTAMP    | Last update                    |
| version         | INTEGER      | Optimistic locking             |

### Audit Logs Table

| Column      | Type         | Description                          |
| ----------- | ------------ | ------------------------------------ |
| id          | UUID         | Primary key                          |
| tenant_id   | UUID         | Foreign key to tenants               |
| user_id     | UUID         | Foreign key to users (nullable)      |
| event_type  | VARCHAR(50)  | login, logout, signup, refresh, etc. |
| status      | VARCHAR(20)  | success, failure                     |
| action      | VARCHAR(100) | Detailed action                      |
| description | TEXT         | Additional context                   |
| ip_address  | VARCHAR(50)  | Request IP                           |
| user_agent  | TEXT         | Browser/client info                  |
| created_at  | TIMESTAMP    | Event timestamp                      |

## Database Migrations

### Run Migrations

```bash
# All pending migrations
alembic upgrade head

# Specific revision
alembic upgrade 001_initial_schema

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

### Create New Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Encryption Key Generation Guide

### Method 1: Python (Recommended)

```python
import os
from base64 import b64encode

# Generate 256-bit key (32 bytes)
aes_key = os.urandom(32)
print(f"AES_KEY={b64encode(aes_key).decode()}")

# Generate 128-bit IV (16 bytes)
aes_iv = os.urandom(16)
print(f"AES_IV={b64encode(aes_iv).decode()}")
```

### Method 2: OpenSSL

```bash
# Generate key
openssl rand -base64 32

# Generate IV
openssl rand -base64 16
```

### Method 3: Linux/Mac

```bash
# Key
head -c 32 /dev/urandom | base64

# IV
head -c 16 /dev/urandom | base64
```

## Testing

### Manual Testing with cURL

```bash
# Create tenant
TENANT_ID=$(curl -X POST http://localhost:8000/api/auth/tenants \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Test Corp","industry":"Tech"}' \
  | jq -r '.id')

# Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"tenant_id\":\"$TENANT_ID\",\"email\":\"test@example.com\",\"password\":\"SecurePass123\",\"name\":\"Test User\"}"

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"tenant_id\":\"$TENANT_ID\",\"email\":\"test@example.com\",\"password\":\"SecurePass123\"}"
```

## Compliance Notes

### DPDP Act Compliance

1. **PII Encryption**: All personal data (name, email) encrypted at rest with AES-256
2. **Data Isolation**: Multi-tenant architecture with strict tenant_id filtering
3. **Audit Trail**: All access logged with user, timestamp, action
4. **Data Retention**: Configurable via `AUDIT_RETENTION_DAYS`
5. **Encryption Key Management**: Keys stored in environment (rotate regularly)

### Future Improvements

1. **Row-Level Security (RLS)**: Enable PostgreSQL RLS policies
2. **Key Rotation**: Implement automatic key rotation mechanism
3. **Encryption Key Vault**: Move from environment to Azure Key Vault/AWS Secrets Manager
4. **Data Deletion**: Implement GDPR "right to be forgotten"
5. **API Rate Limiting**: Per-tenant rate limits
6. **2FA/MFA**: Multi-factor authentication support

## Logging

Logs are output to console in format:

```
2024-01-01 12:00:00,000 - module_name - INFO - Message
```

Configure in `main.py` to forward to centralized logging (ELK, DataDog, etc.)

## Performance Considerations

1. **Database**: Connection pooling (10 connections, max 20 overflow)
2. **Redis**: Caching role permissions with 1-hour TTL
3. **Compression**: Enable gzip compression for JSON responses
4. **Async**: Use async/await for I/O operations (future)

## Next Steps

1. **Create Contract Service**: Handle contract management
2. **Create Compliance Service**: CMS compliance tracking
3. **Create Employment Service**: Employment document generation
4. **API Gateway**: Centralized auth/rate limiting
5. **Admin Dashboard**: Tenant management, audit logs
6. **Frontend**: React/Vue UI for end-users

---

For more information, see [TE Major Project.md](../docs/TE%20Major%20Project.md)
