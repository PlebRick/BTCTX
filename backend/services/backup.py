# backend/services/backup.py

import os
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey
import secrets

# === Constants ===
DB_PATH = Path("backend/bitcoin_tracker.db")
KEY_LENGTH = 32  # AES-256
SALT_LENGTH = 16
IV_LENGTH = 16
PBKDF2_ITERATIONS = 100_000

# === Utils ===
def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())

def _encrypt_data(data: bytes, key: bytes, iv: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()

def _decrypt_data(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

# === Public API ===

def make_backup(password: str, output_file: Path) -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database file not found: {DB_PATH}")

    salt = secrets.token_bytes(SALT_LENGTH)
    iv = secrets.token_bytes(IV_LENGTH)
    key = _derive_key(password, salt)

    with open(DB_PATH, "rb") as f:
        db_data = f.read()

    encrypted = _encrypt_data(db_data, key, iv)

    with open(output_file, "wb") as f:
        f.write(salt + iv + encrypted)

    print(f"✅ Backup created at: {output_file}")

def restore_backup(password: str, encrypted_file: Path) -> None:
    if not encrypted_file.exists():
        raise FileNotFoundError(f"Backup file not found: {encrypted_file}")

    with open(encrypted_file, "rb") as f:
        blob = f.read()

    salt = blob[:SALT_LENGTH]
    iv = blob[SALT_LENGTH:SALT_LENGTH+IV_LENGTH]
    encrypted_data = blob[SALT_LENGTH+IV_LENGTH:]
    key = _derive_key(password, salt)

    try:
        decrypted = _decrypt_data(encrypted_data, key, iv)
    except Exception as e:
        raise ValueError("❌ Failed to decrypt backup. Wrong password?") from e

    with open(DB_PATH, "wb") as f:
        f.write(decrypted)

    print(f"✅ Database restored from: {encrypted_file}")
