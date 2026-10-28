"""
Toy messaging-app sender for the FCM push test.

Usage:
  python send.py --token <TOKEN> --mode leaky --sender Pallak --text "hi"
  python send.py --token <TOKEN> --mode encrypted --sender Pallak --text "hi"
  python send.py --token <TOKEN> --mode sync

Modes mirror the 3 strategies in Samarin et al. (PETS 2024):
  leaky     -> sender + text in plain view (FCM sees everything)
  encrypted -> text AES-GCM encrypted before it reaches FCM
  sync      -> only a message ID; the app would fetch the real message elsewhere
"""
import argparse
import base64
import csv
import json
import os
import uuid
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, messaging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(HERE, "service-account.json")
SHARED_KEY_FILE = os.path.join(HERE, "shared.key")  # AES key the receiver also needs
LOG_FILE = os.path.join(HERE, "sends.csv")


def load_shared_key():
    """Load the 32-byte AES key, or create one the first time."""
    if not os.path.exists(SHARED_KEY_FILE):
        with open(SHARED_KEY_FILE, "w") as f:
            f.write(base64.b64encode(AESGCM.generate_key(bit_length=256)).decode())
        print(f"Created {SHARED_KEY_FILE}. Give this key to the receiver app.")
    with open(SHARED_KEY_FILE) as f:
        return base64.b64decode(f.read().strip())


def send_leaky(token, sender, text):
    """Plain notification: delivery test. Android shows it even if the app is closed."""
    msg = messaging.Message(
        token=token,
        notification=messaging.Notification(title=sender, body=text),
        data={"sender": sender, "text": text},
        android=messaging.AndroidConfig(priority="high"),
    )
    return msg


def send_encrypted(token, sender, text):
    """Data-only message; text is encrypted so FCM only sees ciphertext."""
    nonce = os.urandom(12)
    ciphertext = AESGCM(load_shared_key()).encrypt(nonce, text.encode(), None)
    msg = messaging.Message(
        token=token,
        data={
            "sender": sender,
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
        },
        android=messaging.AndroidConfig(priority="high"),
    )
    return msg


def send_sync(token):
    """Data-only ping carrying just an ID (push-to-sync)."""
    msg = messaging.Message(
        token=token,
        data={"msg_id": str(uuid.uuid4())},
        android=messaging.AndroidConfig(priority="high"),
    )
    return msg


def log_send(mode, msg, message_id):
    """Append what we sent so it can be matched against the receiver's logs."""
    payload = {
        "data": msg.data,
        "notification": vars(msg.notification) if msg.notification else None,
    }
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["time_utc", "mode", "payload", "fcm_message_id"])
        w.writerow([datetime.now(timezone.utc).isoformat(), mode, json.dumps(payload), message_id])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True, help="FCM token from the receiver app")
    p.add_argument("--mode", choices=["leaky", "encrypted", "sync"], default="leaky")
    p.add_argument("--sender", default="Pallak")
    p.add_argument("--text", default="hello from the toy app")
    p.add_argument("--dry-run", action="store_true",
                   help="FCM validates the message and key but does not deliver it")
    args = p.parse_args()

    firebase_admin.initialize_app(credentials.Certificate(KEY_FILE))

    if args.mode == "leaky":
        msg = send_leaky(args.token, args.sender, args.text)
    elif args.mode == "encrypted":
        msg = send_encrypted(args.token, args.sender, args.text)
    else:
        msg = send_sync(args.token)

    message_id = messaging.send(msg, dry_run=args.dry_run)
    if args.dry_run:
        print(f"[{args.mode}] DRY RUN ok (not delivered): {message_id}")
        return
    log_send(args.mode, msg, message_id)
    print(f"[{args.mode}] sent: {message_id}")


if __name__ == "__main__":
    main()
