
Java.perform(function () {
    const FirebaseService = Java.use(
        "com.google.firebase.messaging.FirebaseMessagingService"
    );

    const handleIntent = FirebaseService.handleIntent.overload(
        "android.content.Intent"
    );

    handleIntent.implementation = function (intent) {
        try {
            const action = intent.getAction();
            const extras = intent.getExtras();
            const payload = {};

            if (extras !== null) {
                const keys = extras.keySet().toArray();

                for (let i = 0; i < keys.length; i++) {
                    const key = String(keys[i]);
                    const value = extras.get(key);

                    payload[key] =
                        value === null ? null : String(value);
                }
            }

            console.log(
                "[FRIDA FCM SDK] " +
                JSON.stringify({
                    action: action === null
                        ? null
                        : String(action),
                    extras: payload
                })
            );
        } catch (error) {
            console.log("[FRIDA SDK ERROR] " + error);
        }

        // Always continue normal Firebase processing.
        return handleIntent.call(this, intent);
    };

    console.log("FCM SDK handleIntent hook installed!");
});