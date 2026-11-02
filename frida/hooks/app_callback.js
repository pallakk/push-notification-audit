
Java.perform(function () {
    const PushService = Java.use(
        "com.sfgg.pushtest.PushService"
    );

    const Map = Java.use("java.util.Map");
    const JSONObject = Java.use("org.json.JSONObject");

    const hook = PushService.onMessageReceived.overload(
        "com.google.firebase.messaging.RemoteMessage"
    );

    hook.implementation = function (message) {
        try {
            const data = Java.cast(message.getData(), Map);
            const payload = JSONObject.$new(data).toString();

            console.log("[FRIDA FCM JSON] " + payload);
        } catch (error) {
            console.log("[FRIDA ERROR] " + error);
        }

        return hook.call(this, message);
    };

    console.log("JSON payload hook installed!");
});