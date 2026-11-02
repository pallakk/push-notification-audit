

\# Frida FCM Privacy Collector



\## Overview



This directory contains Frida instrumentation scripts for

observing Firebase Cloud Messaging (FCM) payloads in

Android applications.



The initial implementation instruments our controlled

Push Receiver test application.



\## Environment



\- Android 14 (API 34) rooted emulator

\- Frida 17.24.3

\- Matching Android frida-server

\- Android Debug Bridge (ADB)

\- Test application: com.sfgg.pushtest



\## Current Hook



`hooks/app\_callback.js`



Intercepts the test application's

`PushService.onMessageReceived()` method.



The hook:

1\. Observes incoming FCM data messages.

2\. Extracts the data payload.

3\. Converts it to JSON.

4\. Prints the captured fields to the Frida console.

5\. Calls the original message handler.



\## Running the Collector



Ensure the Android emulator and Frida server are running.



Find the app's current process ID:



&#x20;   frida-ps -Uai



Attach and load the script:



&#x20;   frida -U -p <PID> -l frida/hooks/app\_callback.js



Replace <PID> with the running application's process ID.

Run these commands from the repository root.



\## Verified Test Cases



| Mode | Observed FCM data |

|------|-------------------|

| Leaky | Sender and plaintext message |

| Encrypted | Sender, ciphertext, and nonce |

| Push-to-sync | Message identifier only |



All three modes were captured successfully using

the application-specific Frida callback hook.



\## Limitations



\- The current hook targets our controlled application.

\- It only observes messages reaching onMessageReceived().

\- Background notification handling may bypass this callback.

\- Missing captures do not establish that a message is private.

\- Push-to-sync currently simulates an ID-only notification

&#x20; without retrieving message content from a backend.



\## Next Steps



\- Generalize instrumentation to Firebase SDK methods.

\- Record structured JSONL capture logs.

\- Evaluate foreground and background notification coverage.

\- Integrate automated testing and privacy classification.

\- Apply the methodology to selected health applications.

