import secrets
import hashlib

def generate_pin(length=4):
    pin = ''.join(secrets.choice('0123456789') for _ in range(length))
    pin_hash = hashlib.sha256(pin.encode()).hexdigest()
    return pin, pin_hash

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()