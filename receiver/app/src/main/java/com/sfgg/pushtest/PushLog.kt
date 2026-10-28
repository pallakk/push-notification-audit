package com.sfgg.pushtest

import android.content.Context
import android.util.Base64
import android.util.Log
import org.json.JSONObject
import java.io.File
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Everything the app writes goes to the app's folder on the phone:
 *   /sdcard/Android/data/com.sfgg.pushtest/files/token.txt     <- FCM token
 *   /sdcard/Android/data/com.sfgg.pushtest/files/pushes.jsonl  <- one line per push received
 * and also to logcat with tag PUSHTEST.
 */
object PushLog {
    const val TAG = "PUSHTEST"

    private fun dir(ctx: Context): File = ctx.getExternalFilesDir(null) ?: ctx.filesDir

    fun logFile(ctx: Context): File = File(dir(ctx), "pushes.jsonl")

    fun saveToken(ctx: Context, token: String) {
        File(dir(ctx), "token.txt").writeText(token)
        Log.i(TAG, "FCM token: $token")
    }

    @Synchronized
    fun append(ctx: Context, entry: JSONObject) {
        logFile(ctx).appendText(entry.toString() + "\n")
        Log.i(TAG, entry.toString())
    }

    fun recent(ctx: Context, n: Int): List<String> {
        val f = logFile(ctx)
        if (!f.exists()) return emptyList()
        return f.readLines().filter { it.isNotBlank() }.takeLast(n).reversed()
    }

    fun hasKey(): Boolean = BuildConfig.SHARED_KEY.isNotEmpty()

    /** Mirrors send.py: AES-256-GCM, 12-byte nonce, ciphertext includes the 16-byte tag. */
    fun decrypt(ciphertextB64: String, nonceB64: String): String {
        require(hasKey()) { "app was built without shared.key" }
        val key = Base64.decode(BuildConfig.SHARED_KEY, Base64.DEFAULT)
        val nonce = Base64.decode(nonceB64, Base64.DEFAULT)
        val ct = Base64.decode(ciphertextB64, Base64.DEFAULT)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "AES"), GCMParameterSpec(128, nonce))
        return String(cipher.doFinal(ct), Charsets.UTF_8)
    }
}
