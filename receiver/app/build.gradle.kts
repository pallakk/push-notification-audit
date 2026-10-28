plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.gms.google-services")
}

// The AES key send.py uses for "encrypted" mode lives one folder up (push-sender/shared.key).
// It gets baked into the app at build time so the app can decrypt. shared.key itself is gitignored.
val sharedKeyFile = rootProject.file("../shared.key")
val sharedKey = if (sharedKeyFile.exists()) sharedKeyFile.readText().trim() else ""

android {
    namespace = "com.sfgg.pushtest"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.sfgg.pushtest"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1"
        buildConfigField("String", "SHARED_KEY", "\"$sharedKey\"")
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation(platform("com.google.firebase:firebase-bom:33.7.0"))
    implementation("com.google.firebase:firebase-messaging")
}
