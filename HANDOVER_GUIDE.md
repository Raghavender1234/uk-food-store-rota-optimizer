# 📱 UK Food Store Rota - Handover & Android Deployment Guide

This guide explains how to hand over the **UK Food Store Rota System** to any store manager or staff member so they can run and use it on an **Android phone, tablet, or PC**.

---

## 🚀 3 Ways to Hand This Over

| Method | Best For | Technical Effort | Time to Install |
| :--- | :--- | :--- | :--- |
| **Option 1: Instant Android Install (PWA)** | **Store Managers & Team Members** | ⭐ Zero setup | **5 seconds** |
| **Option 2: Native Android Studio Project** | **IT / Developers building `.apk`** | ⭐⭐⭐ Build via Gradle | **2 minutes** |
| **Option 3: 1-Click Free Cloud Hosting** | **24/7 Remote Access Anywhere** | ⭐⭐ Upload to cloud | **3 minutes** |

---

## 📲 Option 1: Instant Android Install (PWA - Recommended)

The application is certified as a **Progressive Web App (PWA)**. Any store manager with an Android phone (Samsung, Google Pixel, Xiaomi, Motorola, etc.) can install it in 5 seconds without needing cables, APK sideloading, or developer mode.

### Steps for the Store Manager:
1. Connect the phone to the store's Wi-Fi network.
2. Open **Google Chrome** on the phone and go to:
   ```
   http://<HOST_IP>:5055
   ```
   *(or your store's cloud URL)*
3. Chrome will automatically show an **"Install UK Store Rota"** prompt at the bottom of the screen.
   *(Or tap the 3 vertical dots at the top right $\rightarrow$ tap **"Install App"** or **"Add to Home Screen"**)*.
4. Tap **Install**.

### What Happens:
* A native **"UK Rota"** icon appears on their Android home screen and in their app drawer.
* When tapped, it opens in **Full-Screen Standalone Mode** with zero browser address bars.
* It works with full touch gestures, instant timetable filters, and one-click CSV downloads.

---

## 🤖 Option 2: Native Android Application (Gradle / Android Studio)

A complete native Android project has been generated in the project folder:
```
C:\Users\brred\.gemini\antigravity\scratch\milton_keynes_rota\android_app\
```

### Key Technical Architecture:
* **UI**: Modern **Jetpack Compose** + Hardware-Accelerated WebView.
* **Storage**: Android `SharedPreferences` to save and switch server URLs.
* **Downloads**: Android native `DownloadManager` intercepts CSV export and downloads `store_rota.csv` directly into the phone's public `Downloads/` directory with notification alerts.
* **Offline / Recovery Screen**: If the computer is turned off or the IP changes, the app shows an in-app **Settings Dialog** allowing the user to type in a new server IP or domain.

### How to Build the APK:
1. Open terminal inside the project directory:
   ```bash
   cd android_app
   ```
2. Build the debug APK using the Gradle wrapper:
   ```bash
   ./gradlew assembleDebug
   ```
3. The installable APK will be ready at:
   ```
   android_app/app/build/outputs/apk/debug/app-debug.apk
   ```
4. Send `app-debug.apk` via WhatsApp, Bluetooth, or Google Drive to the manager's phone. Tap on the file to install.

---

## ☁️ Option 3: Free 24/7 Cloud Hosting (No Computer Needed)

If the manager wants to check and edit the rota from **home**, while traveling, or when the store computer is turned off:

You can deploy this Python backend for **free** on platforms like **Render**, **Railway**, or **PythonAnywhere**:

### Quick Deploy to Render.com (Free Tier):
1. Create a free account at [render.com](https://render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select your repository (or upload the folder).
4. Set the build & start commands:
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python app.py`
5. Render gives you a permanent secure HTTPS URL:
   ```
   https://milton-keynes-rota.onrender.com
   ```
6. Anyone can open this link on their Android phone or PC from anywhere in the world!

---

## 📖 Store Manager Quick Reference Card

Print or share this 1-page summary with the store manager:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               UK FOOD STORE ROTA - MANAGER CHEAT SHEET                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. HOW TO ACCESS:                                                           │
│    • From Android Phone: Open Chrome -> http://<HOST_IP>:5055               │
│      Tap "Install App" to add the UK Rota icon to your phone screen.        │
│                                                                             │
│ 2. HOW TO ADD RULES (Tab 2: "Rules & Boundaries"):                          │
│    • Scope: Pick 🔒 GLOBAL (Permanent) or ⚡ LOCAL (This week only)         │
│    • Target: Select employee name or "Entire Store (ALL)"                   │
│    • Rule: Select condition (Latest finish, Blocked days, Hours cap, etc.) │
│    • Click "Save & Enforce Boundary" -> Timetable recalculates instantly.   │
│                                                                             │
│ 3. HOW TO TALK TO AI (Tab 5: "AI Chat Assistant"):                          │
│    • "Jordan works up to 2pm on Monday"                                     │
│    • "Morgan is off this coming Thursday and Friday"                        │
│    • "Limit Casey to 20 hours next week"                                    │
│    • "Generate Pay-Weekend Powerhouse Rota"                                 │
│                                                                             │
│ 4. ACCIDENTAL DELETE RECOVERY:                                              │
│    • Go to Tab 3 ("Staff Directory")                                        │
│    • Click "🔄 Reset to UK Food Store Template" to restore sample roster.   │
│                                                                             │
│ 5. EXPORT FOR PRINTING:                                                     │
│    • Click "📥 Export CSV" in the top bar to download the Excel rota.       │
│                                                                             │
│ 6. EMERGENCY REPLACEMENT:                                                   │
│    • Go to Tab 4 ("Emergency Cover") -> Pick absent person -> see certified │
│      replacements ranked by skill match and availability.                   │
└─────────────────────────────────────────────────────────────────────────────┘
```
