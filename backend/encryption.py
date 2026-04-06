from cryptography.fernet import Fernet
import os

KEY_PATH = os.getenv("ENCRYPTION_KEY_PATH", "./.encryption.key")


def get_or_create_key():
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
    return key


def get_fernet():
    key = get_or_create_key()
    return Fernet(key)


def encrypt_value(value: str) -> str:
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
