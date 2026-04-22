"""Seed a local email account for testing SMTP send endpoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from core import email_crypto  # type: ignore  # noqa: E402
from core.database import init_db, SessionLocal  # type: ignore  # noqa: E402
from crud.email import upsert_email_account  # type: ignore  # noqa: E402

def seed_account(
    user_id: int,
    email: str,
    password: str,
    host: str,
    port: int,
    use_ssl: bool,
) -> None:
    init_db()
    db = SessionLocal()
    try:
        upsert_email_account(
            db,
            user_id=user_id,
            email=email,
            password=email_crypto.encrypt_password_for_storage(password),
            host=host,
            port=port,
            use_ssl=use_ssl,
        )
        print(f"Seeded email_account user_id={user_id} -> {host}:{port}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed email account for SMTP testing.")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--email", type=str, default="test@local")
    parser.add_argument("--password", type=str, default="ignored-for-smtp-debug")
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--use-ssl", action="store_true", default=False)

    args = parser.parse_args()
    seed_account(
        user_id=args.user_id,
        email=args.email,
        password=args.password,
        host=args.host,
        port=args.port,
        use_ssl=args.use_ssl,
    )
