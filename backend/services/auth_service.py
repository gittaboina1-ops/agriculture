"""
Authentication and User Management Service for AgriGraph.
Provides:
- PBKDF2-HMAC-SHA256 password hashing with random salt (cryptographically secure, zero external binary dependency)
- HMAC-SHA256 based JWT encoding and decoding
- Role-Based Access Control (RBAC) for 'farmer' and 'admin'
- Safe MongoDB persistence with in-memory resilient fallback
- Demo account auto-seeding
"""

import os
import hmac
import hashlib
import base64
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from backend.config import settings
from backend.services.mongo_service import mongo_service

logger = logging.getLogger("auth_service")

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _base64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode(data_str + padding)

class AuthService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET.encode("utf-8")
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        # Initialize users storage in mock_db if live MongoDB isn't running
        if "users" not in mongo_service.mock_db:
            mongo_service.mock_db["users"] = []
        self.users_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "users.json")
        self._load_fallback_users()
        self._ensure_indexes_and_seed()
        self._save_fallback_users()

    def _load_fallback_users(self):
        """Loads users from local persistent JSON store if running in fallback mode."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    saved_users = json.load(f)
                    if isinstance(saved_users, list):
                        mongo_service.mock_db["users"] = saved_users
            except Exception as e:
                logger.warning(f"Could not load users from {self.users_file}: {e}")

    def _save_fallback_users(self):
        """Saves fallback users to local JSON store to persist across process restarts."""
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(mongo_service.mock_db["users"], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist users to {self.users_file}: {e}")

    def _ensure_indexes_and_seed(self):
        """Ensures unique email indexing on MongoDB and seeds default admin and demo accounts."""
        if mongo_service.connected and mongo_service.client:
            try:
                db = mongo_service.client[settings.MONGODB_DB]
                db.users.create_index("email", unique=True)
            except Exception as e:
                logger.warning(f"Failed to create user index on MongoDB: {e}")

        # Seed Default Hackathon Admin account
        default_admin_email = getattr(settings, "DEFAULT_ADMIN_EMAIL", "vundhyalaakeshreddy@gmail.com").strip().lower()
        default_admin_password = getattr(settings, "DEFAULT_ADMIN_PASSWORD", "reddy@123")
        if not self.get_user_by_email(default_admin_email):
            self.create_user(
                name="Admin",
                email=default_admin_email,
                password=default_admin_password,
                role="admin"
            )
            logger.info(f"Default Admin user seeded: {default_admin_email}")

        # Seed Demo Admin and Demo Farmer accounts if not already present
        if not self.get_user_by_email("admin@agrigraph.org"):
            self.create_user(
                name="AgriGraph Administrator",
                email="admin@agrigraph.org",
                password="adminpassword123",
                role="admin"
            )
            logger.info("Demo Admin user seeded: admin@agrigraph.org")

        if not self.get_user_by_email("farmer@agrigraph.org"):
            self.create_user(
                name="Ramesh Patel (Farmer)",
                email="farmer@agrigraph.org",
                password="farmerpassword123",
                role="farmer"
            )
            logger.info("Demo Farmer user seeded: farmer@agrigraph.org")

    def hash_password(self, password: str) -> str:
        """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a 16-byte random salt."""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return f"{salt.hex()}${key.hex()}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies plain password against stored salt$hash."""
        try:
            salt_hex, key_hex = hashed_password.split("$")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            derived_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
            return hmac.compare_digest(expected_key, derived_key)
        except Exception:
            return False

    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Creates an HMAC-SHA256 signed JWT token."""
        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        exp = now + (self.expire_minutes * 60)
        
        payload = {
            "sub": str(user_data["id"]),
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"],
            "iat": now,
            "exp": exp
        }

        header_b64 = _base64url_encode(json.dumps(header).encode("utf-8"))
        payload_b64 = _base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        
        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = _base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies JWT signature and expiry. Returns payload dict or None."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
            actual_sig = _base64url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(time.time()):
                return None  # Expired

            return payload
        except Exception:
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email_clean = email.strip().lower()
        if mongo_service.connected and mongo_service.client:
            try:
                db = mongo_service.client[settings.MONGODB_DB]
                doc = db.users.find_one({"email": email_clean})
                if doc:
                    doc["id"] = str(doc.get("_id", doc.get("id")))
                    return doc
            except Exception:
                pass
        
        # Memory fallback
        for u in mongo_service.mock_db["users"]:
            if u["email"].lower() == email_clean:
                return u
        return None

    def create_user(self, name: str, email: str, password: str, role: str = "farmer") -> Dict[str, Any]:
        email_clean = email.strip().lower()
        if self.get_user_by_email(email_clean):
            raise ValueError("An account with this email already exists. Please log in.")

        user_id = f"USR_{int(time.time() * 1000)}"
        user_record = {
            "id": user_id,
            "name": name.strip(),
            "email": email_clean,
            "password_hash": self.hash_password(password),
            "role": role,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

        if mongo_service.connected and mongo_service.client:
            try:
                db = mongo_service.client[settings.MONGODB_DB]
                db.users.insert_one(user_record.copy())
            except Exception as e:
                logger.warning(f"Error persisting user to MongoDB: {e}")

        mongo_service.mock_db["users"].append(user_record)
        self._save_fallback_users()
        return user_record

auth_service = AuthService()
