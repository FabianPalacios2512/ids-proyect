# test_scrypt.py
from passlib.hash import scrypt
import sys

try:
    password = "testpassword"
    hashed = scrypt.hash(password, N=32768, r=8, p=1)
    print(f"Python version: {sys.version}")
    print(f"Passlib scrypt hasher: {scrypt}")
    print(f"Hashed successfully: {hashed}")

    # Verificar si el hash funciona
    is_valid = scrypt.verify(password, hashed)
    print(f"Verification successful: {is_valid}")

except Exception as e:
    print(f"Error during scrypt test: {e}")
    import traceback
    traceback.print_exc()