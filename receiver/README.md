# push-receiver

Toy Android app that catches the test pushes `send.py` sends through Firebase project `dp-push-test1`.

## What it does
- Shows its FCM token on screen (paste it into `send.py --token`)
- Logs every push it receives, one JSON line each, to:
  - `/sdcard/Android/data/com.sfgg.pushtest/files/pushes.jsonl`
  - logcat, tag `PUSHTEST`
- Decrypts `encrypted` mode using `../shared.key` (baked in at build time)

## Run it
- Open this folder in Android Studio, pick a phone or a **Google Play** emulator, hit Run
- Or install a built APK: `adb install push-receiver.apk`

## Get the token on your laptop
```
adb shell cat /sdcard/Android/data/com.sfgg.pushtest/files/token.txt
```

## Send a test push (from push-sender/)
```
python3 send.py --token <TOKEN> --mode encrypted --text "hi"
```

## Read what arrived
```
adb shell cat /sdcard/Android/data/com.sfgg.pushtest/files/pushes.jsonl
adb logcat -s PUSHTEST
```

## Known gap
A `leaky` push sent while the app is in the background is shown by Android itself and never reaches the app's code, so it is not logged. Keep the app open for leaky tests. `encrypted` and `sync` are always logged.
