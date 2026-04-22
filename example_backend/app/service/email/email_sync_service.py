"""Mailbox synchronization helpers with per-account locking."""

from contextlib import contextmanager
from threading import Lock
from typing import Dict, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from crud import email as email_crud

from .email_logging_service import EmailService


_LOCK_REGISTRY: Dict[str, Lock] = {}
_REGISTRY_GUARD = Lock()


def _lock_key(user_id: int, username: str) -> str:
    return f"{user_id}:{username.lower()}"


def _get_lock(key: str) -> Lock:
    with _REGISTRY_GUARD:
        lock = _LOCK_REGISTRY.get(key)
        if lock is None:
            lock = Lock()
            _LOCK_REGISTRY[key] = lock
        return lock


@contextmanager
def _acquire_mailbox_lock(user_id: int, username: str):
    key = _lock_key(user_id, username)
    lock = _get_lock(key)
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def sync_mailbox(
    db: Session,
    user_id: int,
    *,
    host: str,
    username: str,
    password: str,
    port: int = 993,
    folder: str = "INBOX",
    limit: Optional[int] = 200,
    use_ssl: bool = True,
) -> Tuple[int, int, int]:
    """Fetch emails via IMAP and persist new items for the user."""
    if not username:
        raise ValueError("username is required for mailbox sync")

    with _acquire_mailbox_lock(user_id, username):
        service = EmailService(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
        )

        try:
            service.connect()
            emails: Sequence[dict] = service.fetch_emails(folder=folder, limit=limit)
        finally:
            service.close_connection()

        created, skipped = email_crud.bulk_upsert_emails(db, user_id, emails)
        return len(emails), created, skipped
