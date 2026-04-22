"""Utilities for encrypting/decrypting email credentials."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional, cast

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from core import config

_KEY_DIR: Path = config.EMAIL_KEYS_DIR
_PRIVATE_KEY_PATH: Path = config.EMAIL_PRIVATE_KEY_PATH
_PUBLIC_KEY_PATH: Path = config.EMAIL_PUBLIC_KEY_PATH

_KEY_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_rsa_keypair() -> None:
    if _PRIVATE_KEY_PATH.exists() and _PUBLIC_KEY_PATH.exists():
        return

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    _PRIVATE_KEY_PATH.write_bytes(private_bytes)
    _PUBLIC_KEY_PATH.write_bytes(public_bytes)


_ensure_rsa_keypair()

_PRIVATE_KEY_CACHE: Optional[RSAPrivateKey] = None
_PUBLIC_KEY_CACHE = None


def _get_private_key() -> RSAPrivateKey:
    global _PRIVATE_KEY_CACHE
    if _PRIVATE_KEY_CACHE is None:
        _PRIVATE_KEY_CACHE = cast(
            RSAPrivateKey,
            serialization.load_pem_private_key(
                _PRIVATE_KEY_PATH.read_bytes(), password=None
            ),
        )
    return _PRIVATE_KEY_CACHE


def _get_public_key() -> str:
    global _PUBLIC_KEY_CACHE
    if _PUBLIC_KEY_CACHE is None:
        _PUBLIC_KEY_CACHE = _PUBLIC_KEY_PATH.read_text()
    return _PUBLIC_KEY_CACHE


_fernet_key = (config.EMAIL_CREDENTIAL_SECRET_KEY or "").strip().strip('"').strip("'")
if not _fernet_key:
    raise RuntimeError("EMAIL_CREDENTIAL_SECRET_KEY 未配置，无法加密邮箱凭据")

FERNET = Fernet(_fernet_key.encode("utf-8"))


def get_public_key_pem() -> str:
    """Return the PEM formatted public key for frontend consumption."""

    return _get_public_key()


def decrypt_login_secret(encrypted_b64: str) -> str:
    """Decrypt base64-encoded RSA ciphertext from the frontend."""

    try:
        ciphertext = base64.b64decode(encrypted_b64)
    except Exception as exc:  # pragma: no cover - invalid base64
        raise ValueError("加密密码不是有效的 Base64 字符串") from exc

    private_key = _get_private_key()
    try:
        plain = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:  # pragma: no cover - 解密失败
        raise ValueError("无法解密邮箱密码") from exc

    return plain.decode("utf-8")


def resolve_login_password(
    *, encrypted_password: Optional[str], plaintext_password: Optional[str]
) -> str:
    """Choose the best available password input from the login payload."""

    if encrypted_password:
        return decrypt_login_secret(encrypted_password)
    if plaintext_password:
        return plaintext_password
    raise ValueError("缺少邮箱密码字段，请提供 encrypted_password")


def encrypt_password_for_storage(plaintext: str) -> str:
    """Encrypt plaintext password with Fernet for DB storage."""

    token = FERNET.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_stored_password(token: str) -> str:
    """Decrypt stored Fernet token back to plaintext."""

    try:
        value = FERNET.decrypt(token.encode("utf-8"))
        return value.decode("utf-8")
    except InvalidToken:  # pragma: no cover - 数据损坏或旧数据
        return token