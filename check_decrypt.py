"""
Local check that encrypted mode round-trips: build the message, then decrypt it
with shared.key the way the receiver app would. Sends nothing.
"""
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from send import load_shared_key, send_encrypted

TEXT = "secret test message"

msg = send_encrypted("fake-token", "Pallak", TEXT)
ciphertext = base64.b64decode(msg.data["ciphertext"])
nonce = base64.b64decode(msg.data["nonce"])

print("What FCM would see:", msg.data)
plain = AESGCM(load_shared_key()).decrypt(nonce, ciphertext, None).decode()
print("Decrypted on receiver:", plain)
print("PASS" if plain == TEXT else "FAIL")
