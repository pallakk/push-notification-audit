package com.sfgg.pushtest

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import org.json.JSONObject
import java.time.Instant

/**
 * Called by Firebase when a push arrives.
 * Note: a "leaky" push (has a notification part) sent while the app is in the BACKGROUND
 * is shown by Android itself and never reaches this code, so it won't be logged.
 * Data-only pushes (encrypted, sync) always reach this code.
 */
class PushService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        PushLog.saveToken(this, token)
    }

    override fun onMessageReceived(msg: RemoteMessage) {
        val data = msg.data
        val mode = when {
            data.containsKey("ciphertext") -> "encrypted"
            data.containsKey("msg_id") -> "sync"
            else -> "leaky"
        }

        val dataJson = JSONObject()
        data.forEach { (k, v) -> dataJson.put(k, v) }

        val entry = JSONObject()
            .put("received_at", Instant.now().toString())
            .put("mode", mode)
            .put("fcm_message_id", msg.messageId)
            .put("from", msg.from)
            .put("sent_time_ms", msg.sentTime)
            .put("priority", msg.priority)
            .put("original_priority", msg.originalPriority)
            .put("data", dataJson)

        msg.notification?.let { n ->
            entry.put("notification", JSONObject().put("title", n.title).put("body", n.body))
        }

        val title = data["sender"] ?: msg.notification?.title ?: "Push Receiver"
        var text: String = when (mode) {
            "leaky" -> data["text"] ?: msg.notification?.body ?: "(empty)"
            "sync" -> "New message (id ${data["msg_id"]?.take(8)})"
            else -> "(encrypted)"
        }

        if (mode == "encrypted") {
            try {
                val plain = PushLog.decrypt(data["ciphertext"]!!, data["nonce"]!!)
                entry.put("decrypted_text", plain)
                text = plain
            } catch (e: Exception) {
                entry.put("decrypt_error", e.toString())
                text = "Could not decrypt: ${e.message}"
            }
        }

        PushLog.append(this, entry)
        show(title, text)
    }

    private fun show(title: String, text: String) {
        val nm = getSystemService(NotificationManager::class.java)!!
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL, "Test pushes", NotificationManager.IMPORTANCE_HIGH)
        )
        val n = Notification.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_email)
            .setContentTitle(title)
            .setContentText(text)
            .setAutoCancel(true)
            .build()
        nm.notify((System.currentTimeMillis() % Int.MAX_VALUE).toInt(), n)
    }

    companion object {
        const val CHANNEL = "pushes"
    }
}
