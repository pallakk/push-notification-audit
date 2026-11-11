
"""Reusable Frida-based FCM payload collector."""

import argparse
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import frida


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "frida" / "build" / "firebase_agent.bundle.js"
LOG_DIR = ROOT / "runs"
FCM_PREFIX = "[FRIDA FCM SDK] "


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def collect(package, marker=None):
    LOG_DIR.mkdir(exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output = LOG_DIR / f"{package}_{run_id}.jsonl"

    print(f"[INFO] Target: {package}")
    print(f"[INFO] Output: {output}")

    device = frida.get_usb_device(timeout=10)

    apps = device.enumerate_applications(scope="full")
    app = next(
        (a for a in apps if a.identifier == package and a.pid > 0),
        None,
    )

    if app is None:
        raise RuntimeError(
            f"{package} is not running. Open the app first."
        )

    print(f"[INFO] Found process PID: {app.pid}")

    session = device.attach(app.pid)
    stopped = threading.Event()
    session.on("detached", lambda reason, *args: stopped.set())

    captures = 0
    matches = 0

    with output.open("w", encoding="utf-8") as logfile:

        def write_event(event, **data):
            record = {
                "timestamp": timestamp(),
                "package": package,
                "event": event,
                **data,
            }

            logfile.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )
            logfile.flush()

        def on_message(message, data):
            nonlocal captures, matches

            if message["type"] == "log":
                text = str(message.get("payload", ""))

                if text.startswith(FCM_PREFIX):
                    try:
                        payload = json.loads(
                            text[len(FCM_PREFIX):]
                        )
                    except json.JSONDecodeError as error:
                        write_event(
                            "parse_error",
                            error=str(error),
                            raw_text=text,
                        )
                        print("[ERROR] Could not parse FCM payload.")
                        return

                    captures += 1

                    # Save the complete captured payload.
                    capture_data = {
                        "capture_number": captures,
                        "payload": payload,
                    }

                    # Optional marker detection.
                    if marker is not None:
                        found = marker in json.dumps(
                            payload,
                            ensure_ascii=False,
                        )

                        matches += int(found)
                        capture_data["marker_found"] = found

                    write_event(
                        "fcm_payload",
                        **capture_data,
                    )

                    # Print the complete captured payload.
                    print(
                        f"\n[CAPTURE {captures}] "
                        f"Full FCM SDK payload:"
                    )

                    print(
                        json.dumps(
                            payload,
                            indent=2,
                            ensure_ascii=False,
                        )
                    )

                    if marker is not None:
                        print(
                            f"[MARKER] {marker} "
                            f"found: {found}"
                        )

                    print("-" * 60)

                elif "hook installed" in text:
                    write_event("hook_ready")
                    print("[INFO] Firebase SDK hook ready.")

                elif "[FRIDA SDK ERROR]" in text:
                    write_event(
                        "hook_error",
                        error=text,
                    )
                    print("[ERROR]", text)

            elif message["type"] == "error":
                write_event(
                    "script_error",
                    error=message.get("description"),
                    stack=message.get("stack"),
                )
                print("[ERROR] Frida script error.")
                print(message.get("description"))

        # Load the compiled Frida 17 agent.
        script = session.create_script(
            HOOK.read_text(encoding="utf-8")
        )

        # Forward Frida console logs to Python.
        script.set_log_handler(
            lambda level, text: on_message(
                {"type": "log", "payload": text},
                None,
            )
        )

        # Receive Frida messages and errors.
        script.on("message", on_message)

        try:
            script.load()

            write_event(
                "experiment_started",
                marker=marker,
                pid=app.pid,
            )

            print("[INFO] Collector running.")
            print("[INFO] Recording all observed FCM payloads.")
            print("[INFO] Background the app and trigger a push.")
            print("[INFO] Press Ctrl+C to finish.")

            while not stopped.wait(0.5):
                pass

        except KeyboardInterrupt:
            print("\n[INFO] Stopping collector.")

        finally:
            write_event(
                "experiment_finished",
                captures=captures,
                matches=matches if marker is not None else None,
            )

            try:
                script.unload()
            except frida.InvalidOperationError:
                pass

            try:
                session.detach()
            except frida.InvalidOperationError:
                pass

    print("\n" + "=" * 60)
    print("[RESULT] Experiment complete.")
    print(f"[RESULT] Payloads captured: {captures}")

    if marker is not None:
        print(f"[RESULT] Marker matches: {matches}")

    print(f"[RESULT] Saved to: {output}")

    if captures == 0:
        print(
            "[RESULT] INCONCLUSIVE: "
            "No FCM payloads were captured."
        )
    elif marker is not None and matches == 0:
        print(
            "[RESULT] No matching marker observed. "
            "Privacy status remains inconclusive."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Capture FCM SDK payloads using Frida."
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Android application package name.",
    )

    parser.add_argument(
        "--marker",
        default=None,
        help="Optional test marker to search for.",
    )

    args = parser.parse_args()

    collect(args.package, args.marker)


if __name__ == "__main__":
    main()
