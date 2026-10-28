package com.sfgg.pushtest

import android.Manifest
import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import com.google.firebase.messaging.FirebaseMessaging

/** One screen: shows the FCM token (to paste into send.py) and the last pushes received. */
class MainActivity : Activity() {

    private lateinit var tokenView: TextView
    private lateinit var logView: TextView
    private var token: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val pad = (16 * resources.displayMetrics.density).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad * 2, pad, pad)
        }

        root.addView(TextView(this).apply {
            text = "Push Receiver"
            textSize = 22f
        })
        root.addView(TextView(this).apply {
            text = if (PushLog.hasKey()) "Shared key: loaded" else "Shared key: MISSING (encrypted mode won't decrypt)"
        })

        tokenView = TextView(this).apply {
            text = "Getting FCM token..."
            setTextIsSelectable(true)
            setPadding(0, pad, 0, pad)
        }
        root.addView(tokenView)

        root.addView(Button(this).apply {
            text = "Copy token"
            setOnClickListener { copyToken() }
        })
        root.addView(Button(this).apply {
            text = "Refresh log"
            setOnClickListener { refreshLog() }
        })

        logView = TextView(this).apply {
            setTextIsSelectable(true)
            setPadding(0, pad, 0, 0)
        }
        root.addView(logView)

        setContentView(ScrollView(this).apply { addView(root) })

        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }

        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                token = task.result
                PushLog.saveToken(this, task.result)
                tokenView.text = "FCM token:\n${task.result}"
            } else {
                tokenView.text = "Token error: ${task.exception}"
            }
        }
    }

    override fun onResume() {
        super.onResume()
        refreshLog()
    }

    private fun copyToken() {
        val t = token ?: return
        getSystemService(ClipboardManager::class.java)!!.setPrimaryClip(ClipData.newPlainText("FCM token", t))
        Toast.makeText(this, "Token copied", Toast.LENGTH_SHORT).show()
    }

    private fun refreshLog() {
        val lines = PushLog.recent(this, 20)
        logView.text = if (lines.isEmpty()) {
            "No pushes received yet."
        } else {
            "Last ${lines.size} pushes (newest first):\n\n" + lines.joinToString("\n\n")
        }
    }
}
