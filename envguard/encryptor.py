"""Encrypt and decrypt sensitive values in an env mapping."""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List

_SENSITIVE = {"secret", "password", "passwd", "token", "key", "api", "auth", "private"}


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(s in lower for s in _SENSITIVE)


def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_encrypt(value: str, key: bytes) -> str:
    data = value.encode()
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode()


def _xor_decrypt(token: str, key: bytes) -> str:
    encrypted = base64.urlsafe_b64decode(token.encode())
    data = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted))
    return data.decode()


@dataclass
class EncryptResult:
    encrypted: Dict[str, str]
    skipped: List[str] = field(default_factory=list)
    processed: List[str] = field(default_factory=list)

    @property
    def encrypt_count(self) -> int:
        return len(self.processed)

    def summary(self) -> str:
        return (
            f"Encrypted {self.encrypt_count} value(s), "
            f"skipped {len(self.skipped)} plaintext key(s)."
        )


def encrypt_env(env: Dict[str, str], passphrase: str, all_keys: bool = False) -> EncryptResult:
    key = _derive_key(passphrase)
    encrypted: Dict[str, str] = {}
    processed: List[str] = []
    skipped: List[str] = []
    for k, v in env.items():
        if all_keys or _is_sensitive(k):
            encrypted[k] = _xor_encrypt(v, key)
            processed.append(k)
        else:
            encrypted[k] = v
            skipped.append(k)
    return EncryptResult(encrypted=encrypted, skipped=skipped, processed=processed)


def decrypt_env(env: Dict[str, str], passphrase: str, all_keys: bool = False) -> Dict[str, str]:
    key = _derive_key(passphrase)
    result: Dict[str, str] = {}
    for k, v in env.items():
        if all_keys or _is_sensitive(k):
            try:
                result[k] = _xor_decrypt(v, key)
            except Exception:
                result[k] = v
        else:
            result[k] = v
    return result
