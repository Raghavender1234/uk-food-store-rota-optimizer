# ⚡ AI Rota & Shift Optimization Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Google OR-Tools](https://img.shields.io/badge/Google%20OR--Tools-CP--SAT-green.svg)](https://developers.google.com/optimization)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20PWA%20%7C%20Android-purple.svg)](#client-apps)

An intelligent, constraint-satisfaction shift scheduling system designed for fast-paced hospitality, retail, and restaurant operations. 

Unlike legacy workforce management software that relies on rigid, break-prone templates or forces store managers into hours of manual spreadsheet editing, this engine pairs **Google OR-Tools CP-SAT** mathematical optimization with a **dynamic rule engine and conversational AI parser**. Managers can speak or type constraints naturally (*"Jordan can't work past 2 PM on Mondays"*, *"Sam works Friday and Saturday dinners"*), and the solver generates legally compliant, budget-optimized rotas in under 0.5 seconds.

---

## 🌟 Why This Exists (Solving the Enterprise Rota Problem)

Most enterprise workforce software (e.g., Workforce, Deputy, 7shifts) fails store managers in three critical ways:
1. **The Infeasibility Trap**: If two manager constraints contradict each other, traditional schedulers crash or return blank schedules, forcing the manager to scrap automation and do it manually. This engine utilizes **dynamic soft-constraint relaxation and fallback roles**, ensuring a feasible schedule is always generated.
2. **Ignorance of Operational Reality**: Standard tools don't understand that Monday morning delivery requires a keyholder who can lift stock, or that Friday dinner needs your highest-rated grill master. This engine natively incorporates role weights, keyholder requirements, skill tagging, and peak rush coverage.
3. **High Manager Cognitive Load**: Instead of navigating 20 dropdown menus to book a day off or limit a worker's shift length, managers can issue natural language commands or toggle simple availability matrices.

---

## 🚀 Key Features

- **Multi-Objective Optimization (Google OR-Tools CP-SAT)**:
  - **⚖️ Fair & Balanced**: Equalizes hours across part-time team members while satisfying minimum contract commitments.
  - **⚡ Peak Powerhouse**: Prioritizes highest-skilled veterans (e.g., Team Leaders and Managers) during weekend dinner rushes.
  - **💰 Budget Guardian**: Maximizes salaried management hours (£0 marginal cost) and trims excess staffing to hit strict wage targets.
- **UK Working Time Compliance Built-In**:
  - Automatic 30-minute unpaid break deduction for any shift $\ge 6.0$ hours.
  - Mandatory minimum 2 full rest days per week per employee.
  - Automatic max 1 shift per employee per calendar day.
  - Salaried 45-hour utilization vs. hourly wage calculations.
- **Natural Language Conversational Assistant**:
  - Type or speak instructions: *"Jordan is off next Tuesday"*, *"Cap Morgan at 20 hours"*, *"Set weekly budget to £3,850"*, or *"On Mondays Sam works up to 2pm only"*.
  - Automatically resolves nicknames, shifts, and day-specific timing restrictions.
- **Client Flexibility**:
  - **Desktop / Web Browser**: Responsive dashboard with 1-click optimization, live stats, CSV export, and PDF printing.
  - **Progressive Web App (PWA)**: Installable directly onto iOS and Android home screens without an app store (`/manifest.json`, Service Worker caching).
  - **Native Android Companion**: Kotlin + Jetpack Compose Android app with offline recovery, dynamic server URL switching, and native Android `DownloadManager` integration.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Client Layer                         │
│  - Web Browser (Desktop / Tablet)                      │
│  - PWA (iOS / Android Home Screen)                     │
│  - Android Native App (Jetpack Compose + WebView)      │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP / JSON REST API
┌───────────────────────────▼────────────────────────────┐
│                    Flask Backend                       │
│  - State Management (`store_state.json`)               │
│  - Natural Language Parser (`chat_parser.py`)          │
│  - Dynamic Rule Engine (`app.py`)                      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│              Google OR-Tools CP-SAT                    │
│             (`dynamic_solver.py`)                      │
│  - Integer Linear Programming (ILP) Solver             │
│  - Soft & Hard Constraint Satisfaction                │
│  - Shift-Skill Bipartite Matching                      │
└────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

### Prerequisites
- Python 3.10 or higher
- `git`

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-rota-optimizer.git
cd ai-rota-optimizer
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Initialize Store Data
Copy the sample template to create your store state:
```bash
# Windows PowerShell
Copy-Item store_state.example.json store_state.json

# Linux / macOS
cp store_state.example.json store_state.json
```

### 4. Launch the Server
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5055
```

---

## 📱 Mobile & PWA Access

1. Ensure your computer and smartphone are connected to the same Wi-Fi network.
2. Find your host machine's local IP address (`ipconfig` on Windows or `ifconfig` on Linux/macOS).
3. On your smartphone's browser (Safari or Chrome), open:
   ```
   http://<YOUR_LOCAL_IP>:5055
   ```
4. Tap **Share / Options** $\rightarrow$ **Add to Home Screen** to install as a standalone PWA.

For the native Android app, see the [`android_app/`](android_app/) directory and build with Android Studio or `./gradlew assembleDebug`.

---

## 🔒 Privacy & GDPR Notice

> [!IMPORTANT]
> **Do not commit real employee personal data (names, phone numbers, wages, or leave requests) to public repositories.**
> - Keep `store_state.json` in your local environment or add it to `.gitignore`.
> - Always use `store_state.example.json` with fictional names ("Alex Miller", "Sam Taylor") when publishing, testing, or submitting pull requests.

---

## 📂 Project Structure

```
├── app.py                   # Flask server, REST API, PWA service worker routes
├── dynamic_solver.py        # Google OR-Tools CP-SAT mathematical optimization engine
├── chat_parser.py           # Natural language rule & command extraction engine
├── rota_engine.py           # Legacy rule reference & helpers
├── store_state.example.json # Anonymized demo data template
├── requirements.txt         # Python package dependencies
├── LICENSE                  # MIT License
├── HANDOVER_GUIDE.md        # Complete deployment and store handover documentation
├── android_app/             # Kotlin Jetpack Compose Android Companion Project
└── tests/                   # Verification and benchmark test scripts
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - feel free to use, modify, and distribute it in private or commercial settings.
