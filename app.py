"""
UK Food Store Rota Optimizer - Universal Dynamic Architecture V7
Features:
- UNLIMITED Global & Local Rules (Zero hardcoding in Python).
- Prominent User Dropdown selectors across all screens (Rules, Timetable, Staff, Chat).
- Scope Selector: 🔒 Permanent Global Boundary vs ⚡ Local Boundary (This Week Only).
- Interactive Timetable with "Highlight Team Member" visual filter.
- Dynamic Chat Intent Compiler with alias resolution and typo tolerance.
- Multi-Store Extensibility: Add/Edit/Clear staff, custom wages, salaried manager support.
- Emergency Standby Cover & CSV Export.
"""

from flask import Flask, render_template_string, request, jsonify, Response
import dynamic_solver
import rota_engine
import chat_parser
import json
import os
import csv
import io

app = Flask(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), "store_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading state:", e)
    return {
        "mode": "balanced",
        "is_pay_week": False,
        "weekly_budget": 4000.0,
        "staff_list": rota_engine.DEFAULT_STAFF,
        "store_hours": rota_engine.DEFAULT_GLOBAL_RULES["store_hours"],
        "global_rules": [
            {
                "id": "rule_mandatory_days_off",
                "scope": "GLOBAL",
                "target_type": "STORE",
                "target_id": "ALL",
                "rule_type": "MANDATORY_DAYS_OFF",
                "value": 2,
                "description": "Mandatory 2 Days Off Guarantee: Every worker is guaranteed at least 2 full rest days per week."
            }
        ],
        "local_rules": [],
        "leave": {},
        "cap_overrides": {},
        "rate_overrides": {},
        "add_staff": [],
        "inactive_staff": [],
        "chat_history": [
            {
                "sender": "bot",
                "text": "👋 Welcome to your Universal AI Rota System! You can add unlimited Global (permanent) and Local (this week only) rules using the dropdowns or chat."
            }
        ],
        "current_roster": None
    }

def save_state(s):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception as e:
        print("Save state error:", e)

CURRENT_STATE = load_state()

if "global_rules" not in CURRENT_STATE:
    CURRENT_STATE["global_rules"] = []
if "local_rules" not in CURRENT_STATE:
    CURRENT_STATE["local_rules"] = []
if "store_hours" not in CURRENT_STATE:
    CURRENT_STATE["store_hours"] = rota_engine.DEFAULT_GLOBAL_RULES["store_hours"]
if "staff_list" not in CURRENT_STATE or not CURRENT_STATE["staff_list"]:
    CURRENT_STATE["staff_list"] = rota_engine.DEFAULT_STAFF

def solve_current():
    combined_rules = list(CURRENT_STATE.get("global_rules", [])) + list(CURRENT_STATE.get("local_rules", []))
    return dynamic_solver.solve_universal_rota(
        staff_list=CURRENT_STATE.get("staff_list", []),
        store_hours=CURRENT_STATE.get("store_hours", {}),
        global_rules=combined_rules,
        weekly_rules=CURRENT_STATE,
        mode=CURRENT_STATE.get("mode", "balanced"),
        is_pay_week=CURRENT_STATE.get("is_pay_week", False),
        weekly_budget=CURRENT_STATE.get("weekly_budget", 4000.0)
    )

CURRENT_STATE["current_roster"] = solve_current()
save_state(CURRENT_STATE)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>UK Food Store Rota - Universal AI Manager</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="theme-color" content="#0d1322">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%233b82f6'/><text x='50%' y='55%' font-size='50' font-weight='800' fill='white' dominant-baseline='middle' text-anchor='middle'>UK</text></svg>">
  <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%233b82f6'/><text x='50%' y='55%' font-size='50' font-weight='800' fill='white' dominant-baseline='middle' text-anchor='middle'>MK</text></svg>">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f293d;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --purple: #8b5cf6;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --font: 'Plus Jakarta Sans', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    /* Top Header */
    header {
      background: #0d1322;
      border-bottom: 1px solid var(--card-border);
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      width: 38px;
      height: 38px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.2rem;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .brand-subtitle {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s ease;
      font-family: var(--font);
      text-decoration: none;
    }
    .btn.primary { background: var(--primary); color: white; }
    .btn.primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn.success { background: #059669; color: white; }
    .btn.success:hover { background: #10b981; }
    .btn.danger { background: #dc2626; color: white; }
    .btn.danger:hover { background: #ef4444; }
    .btn.secondary { background: #1e293b; color: var(--text); border-color: #334155; }
    .btn.secondary:hover { background: #334155; }

    /* Nav Tabs */
    .tabs-bar {
      background: #0b1120;
      border-bottom: 1px solid var(--card-border);
      padding: 0 24px;
      display: flex;
      gap: 4px;
      overflow-x: auto;
    }
    .tab-btn {
      padding: 12px 18px;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }
    .badge-count {
      background: #1e293b;
      color: var(--text);
      font-size: 0.7rem;
      padding: 2px 7px;
      border-radius: 12px;
      font-weight: 700;
    }
    .tab-btn.active .badge-count {
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
    }

    /* Content Area */
    .content-area {
      flex: 1;
      padding: 20px 24px;
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
    }
    .tab-pane { display: none; }
    .tab-pane.active { display: block; }

    /* KPI Summary Strip */
    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .kpi-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
    .kpi-value { font-size: 1.45rem; font-weight: 800; font-family: var(--font-mono); }
    .kpi-sub { font-size: 0.75rem; color: var(--text-muted); }

    .manager-quick-bar {
      background: #111827;
      border: 1px solid #1f2937;
      border-left: 4px solid var(--primary);
      border-radius: var(--radius);
      padding: 16px 20px;
      margin-bottom: 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    /* Filter Bar for Timetable */
    .filter-bar {
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 12px 16px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
    }
    .filter-group {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .filter-label {
      font-size: 0.82rem;
      font-weight: 700;
      color: #93c5fd;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .select-styled {
      background: #1e293b;
      color: white;
      border: 1px solid #334155;
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      outline: none;
      cursor: pointer;
    }
    .select-styled:focus { border-color: var(--primary); }

    /* Timetable Grid */
    .timetable-grid {
      display: grid;
      grid-template-columns: repeat(7, minmax(180px, 1fr));
      gap: 12px;
      overflow-x: auto;
      padding-bottom: 12px;
    }
    @media (max-width: 1400px) {
      .timetable-grid { grid-template-columns: repeat(7, minmax(210px, 1fr)); }
    }
    .day-col {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .day-header {
      background: #0d1527;
      padding: 12px 14px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    .day-title { font-weight: 800; font-size: 0.95rem; }
    .day-stats { font-size: 0.72rem; color: var(--text-muted); font-weight: 600; }
    .shifts-stack {
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-height: 480px;
    }
    .shift-card {
      background: #151e33;
      border: 1px solid #23314d;
      border-radius: 8px;
      padding: 10px;
      transition: all 0.15s ease;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .shift-card:hover {
      border-color: #3b82f6;
      background: #1a2540;
    }
    .shift-card.highlighted {
      border: 2px solid #fbbf24 !important;
      background: #2a2412 !important;
      box-shadow: 0 0 14px rgba(245, 158, 11, 0.45);
      animation: pulseHighlight 1.5s infinite alternate;
    }
    @keyframes pulseHighlight {
      0% { transform: scale(1); }
      100% { transform: scale(1.02); }
    }
    .shift-card.dimmed {
      opacity: 0.25;
      filter: grayscale(80%);
    }
    .shift-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .shift-emp-name {
      font-size: 0.88rem;
      font-weight: 700;
      color: white;
    }
    .shift-role-desc {
      font-size: 0.74rem;
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .pill {
      font-size: 0.68rem;
      padding: 2px 6px;
      border-radius: 4px;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      width: fit-content;
    }
    .pill.foh { background: #0369a1; color: #bae6fd; }
    .pill.kitchen { background: #b45309; color: #fde68a; }
    .pill.mgmt { background: #6d28d9; color: #e9d5ff; }
    .pill.salaried { background: #065f46; color: #a7f3d0; }
    .shift-foot {
      display: flex;
      justify-content: space-between;
      font-size: 0.72rem;
      color: var(--text-muted);
      border-top: 1px dashed #23314d;
      padding-top: 5px;
      margin-top: 2px;
    }

    /* Forms & Rules Layout */
    .form-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .form-group label {
      font-size: 0.8rem;
      font-weight: 700;
      color: #cbd5e1;
    }
    .form-control {
      background: #1a2234;
      border: 1px solid #2d3b55;
      padding: 9px 12px;
      border-radius: 8px;
      color: white;
      font-size: 0.85rem;
      font-family: var(--font);
      outline: none;
    }
    .form-control:focus { border-color: var(--primary); }

    /* Scope Toggle Buttons */
    .scope-selector {
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }
    .scope-opt {
      flex: 1;
      padding: 10px;
      border-radius: 8px;
      border: 2px solid #2d3b55;
      background: #131b2e;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.15s ease;
    }
    .scope-opt input { cursor: pointer; }
    .scope-opt.selected-global {
      border-color: #f59e0b;
      background: rgba(245, 158, 11, 0.12);
    }
    .scope-opt.selected-local {
      border-color: #38bdf8;
      background: rgba(56, 189, 248, 0.12);
    }
    .scope-title { font-size: 0.85rem; font-weight: 700; }
    .scope-desc { font-size: 0.72rem; color: var(--text-muted); }

    /* Days Checkbox Picker */
    .days-picker {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 4px;
    }
    .day-chk-btn {
      background: #1e293b;
      border: 1px solid #334155;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      user-select: none;
    }
    .day-chk-btn input { cursor: pointer; }

    /* Rules Grid */
    .rules-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }
    .rule-card {
      background: #131b2e;
      border: 1px solid #23314d;
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 10px;
    }
    .rule-card.global { border-left: 4px solid #f59e0b; }
    .rule-card.local { border-left: 4px solid #38bdf8; }
    .rule-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
    }
    .rule-type-badge {
      font-size: 0.75rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .rule-card.global .rule-type-badge { color: #f59e0b; }
    .rule-card.local .rule-type-badge { color: #38bdf8; }
    .rule-desc {
      font-size: 0.85rem;
      color: #e2e8f0;
      line-height: 1.4;
    }
    .rule-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      border-top: 1px solid #1f293d;
      padding-top: 8px;
    }

    /* Staff Table */
    .table-container {
      overflow-x: auto;
      border-radius: 10px;
      border: 1px solid var(--card-border);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.85rem;
    }
    th {
      background: #0d1527;
      padding: 12px 14px;
      color: #94a3b8;
      font-weight: 700;
      border-bottom: 1px solid var(--card-border);
    }
    td {
      padding: 12px 14px;
      border-bottom: 1px solid #172033;
    }
    tr:hover td { background: #131c30; }

    /* Chat Layout */
    .chat-layout {
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 20px;
      height: 700px;
    }
    @media (max-width: 992px) {
      .chat-layout { grid-template-columns: 1fr; height: auto; }
    }
    .chat-main {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .msg-bubble {
      max-width: 80%;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 0.88rem;
      line-height: 1.5;
    }
    .msg-bubble.user {
      align-self: flex-end;
      background: #2563eb;
      color: white;
      border-bottom-right-radius: 2px;
    }
    .msg-bubble.bot {
      align-self: flex-start;
      background: #1e293b;
      color: #f1f5f9;
      border-bottom-left-radius: 2px;
      border: 1px solid #334155;
    }
    .chat-input-bar {
      padding: 14px;
      background: #0b1120;
      border-top: 1px solid var(--card-border);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .chat-text-row {
      display: flex;
      gap: 10px;
    }
    .chat-composer-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      background: #111a2e;
      padding: 10px;
      border-radius: 8px;
      border: 1px dashed #23314d;
    }
    .chat-hints {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .hint-chip {
      background: #1e293b;
      color: #94a3b8;
      font-size: 0.72rem;
      padding: 4px 10px;
      border-radius: 14px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .hint-chip:hover {
      background: #334155;
      color: white;
    }
  </style>
</head>
<body>

  <!-- TOP HEADER -->
  <header>
    <div class="brand">
      <div class="brand-logo">UK</div>
      <div>
        <div class="brand-title">UK Food Store Rota Optimizer</div>
        <div class="brand-subtitle">Universal Constraint Optimizer · Powered by Google OR-Tools CP-SAT</div>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn secondary" onclick="regenerateRota('balanced')">🔄 Re-Optimize (Balanced)</button>
      <button class="btn primary" onclick="regenerateRota('powerhouse')">⚡ Pay-Weekend Powerhouse</button>
      <a href="/api/export_csv" class="btn success">📥 Export CSV</a>
    </div>
  </header>

  <!-- NAVIGATION TABS -->
  <div class="tabs-bar">
    <button class="tab-btn active" data-tab="timetable" onclick="switchTab('timetable')">
      📅 Weekly Timetable
    </button>
    <button class="tab-btn" data-tab="rules" onclick="switchTab('rules')">
      ⚖️ Rules & Boundaries <span class="badge-count" id="rulesBadge">0</span>
    </button>
    <button class="tab-btn" data-tab="staff" onclick="switchTab('staff')">
      👥 Staff Directory & Wages <span class="badge-count" id="staffBadge">0</span>
    </button>
    <button class="tab-btn" data-tab="controls" onclick="switchTab('controls')">
      ⚡ Weekly Controls & Holidays
    </button>
    <button class="tab-btn" data-tab="chat" onclick="switchTab('chat')">
      💬 AI Chat Assistant
    </button>
    <button class="tab-btn" data-tab="emergency" onclick="switchTab('emergency')">
      🚨 Emergency Standby Cover
    </button>
  </div>

  <!-- MAIN CONTENT CONTAINER -->
  <div class="content-area">

    <!-- KPI STRIP -->
    <div class="kpi-strip">
      <div class="kpi-card">
        <span class="kpi-label">Weekly Scheduled Hours</span>
        <span class="kpi-value" id="kpiHours">0.0h</span>
        <span class="kpi-sub">57 Operational Shift Slots</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Variable Hourly Payroll</span>
        <span class="kpi-value" style="color:#10b981;" id="kpiSpend">£0.00</span>
        <span class="kpi-sub" id="kpiSalariedNote">GM Salaried (£0.00 cost)</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Labor Budget Envelope</span>
        <span class="kpi-value" id="kpiBudget">£4,000.00</span>
        <span class="kpi-sub" id="kpiVariance">Under budget</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Active Store Rules</span>
        <span class="kpi-value" id="kpiRules">0</span>
        <span class="kpi-sub" id="kpiRulesBreakdown">0 Global · 0 Local</span>
      </div>
    </div>

    <!-- TAB 1: TIMETABLE -->
    <div class="tab-pane active" id="pane-timetable">

      <!-- MANAGER ONE-TOUCH CONTROL STUDIO -->
      <div class="manager-quick-bar">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
          <div>
            <div style="font-size:1.15rem; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:8px;">
              <span>⚡ Store Manager 1-Click Rota Studio</span>
            </div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">
              Instant AI recalculation · All 19 store team members · Auto-deducts 30m break & guarantees 2 rest days
            </div>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn secondary" onclick="regenerateRota('balanced')">⚖️ Fair & Balanced</button>
            <button class="btn primary" onclick="regenerateRota('powerhouse')">⚡ Pay-Weekend Powerhouse</button>
            <a href="/api/export_csv" class="btn success">📥 Export to Excel (CSV)</a>
          </div>
        </div>

        <!-- Quick Natural Spoken English Bar -->
        <div style="display:flex; gap:8px; margin-bottom:10px;">
          <input type="text" id="quickCommandInput" class="form-control" placeholder="💬 Type or say a change (e.g. 'Stella finishes by 2pm Monday', 'Barry is off this Friday', 'Limit Raghavender to 25h')..." onkeydown="if(event.key==='Enter') executeQuickCommand()" />
          <button class="btn primary" onclick="executeQuickCommand()" style="white-space:nowrap; padding:10px 18px; font-weight:700;">⚡ Apply & Re-Solve</button>
        </div>

        <!-- Quick 1-Click Action Chips & Fast Day Off -->
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
          <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:700;">Quick Shortcuts:</span>
            <span class="hint-chip" onclick="quickChat('Stella works up to 2pm on Monday')">⏰ Stella: 7-2 Mon</span>
            <span class="hint-chip" onclick="quickChat('Barry is off this Thursday and Friday')">🏖️ Barry: Off Thu/Fri</span>
            <span class="hint-chip" onclick="quickChat('Limit Raghavender to 25 hours next week')">⏱️ Raghavender: 25h</span>
            <span class="hint-chip" onclick="quickChat('Albert never closes and doesn\'t work in mornings')">🚫 Albert: No Close/Morn</span>
            <span class="hint-chip" onclick="quickChat('Reset all overrides')">🔄 Reset This Week</span>
          </div>

          <!-- Quick Day-Off Dropper -->
          <div style="display:flex; gap:6px; align-items:center;">
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:700;">Mark Day Off:</span>
            <select id="quickStaffOffSelect" class="select-styled" style="padding:5px 8px; font-size:0.78rem;">
              <option value="">-- Worker --</option>
            </select>
            <select id="quickDayOffSelect" class="select-styled" style="padding:5px 8px; font-size:0.78rem;">
              <option value="Mon">Mon</option>
              <option value="Tue">Tue</option>
              <option value="Wed">Wed</option>
              <option value="Thu">Thu</option>
              <option value="Fri">Fri</option>
              <option value="Sat">Sat</option>
              <option value="Sun">Sun</option>
            </select>
            <button class="btn secondary" onclick="quickMarkOff()" style="padding:5px 12px; font-size:0.78rem; font-weight:700;">Mark OFF</button>
          </div>
        </div>
      </div>

      <!-- Visible Staff Highlight Dropdown Filter -->
      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">👤 Highlight Team Member:</span>
          <select id="timetableStaffFilter" class="select-styled" onchange="applyStaffHighlight()">
            <option value="ALL">👁️ View All Staff Members (Full Store View)</option>
            <!-- Populated dynamically -->
          </select>
        </div>
        <div id="highlightSummary" style="font-size:0.82rem; color:#f59e0b; font-weight:700;"></div>
      </div>

      <!-- Timetable 7-Day Grid -->
      <div class="timetable-grid" id="timetableGrid">
        <!-- Rendered dynamically -->
      </div>
    </div>

    <!-- TAB 2: RULES & BOUNDARIES MANAGER -->
    <div class="tab-pane" id="pane-rules">
      <!-- Form to Add Unlimited Global or Local Rules -->
      <div class="form-box">
        <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:14px; display:flex; align-items:center; gap:8px;">
          <span>➕ Add Store Boundary / Condition</span>
          <span style="font-size:0.75rem; color:var(--text-muted); font-weight:500;">(Add unlimited Global or Local rules)</span>
        </h3>

        <!-- Scope Selector: Global vs Local -->
        <label style="font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px; display:block;">Select Rule Scope:</label>
        <div class="scope-selector">
          <div class="scope-opt selected-global" id="optScopeGlobal" onclick="setScopeChoice('GLOBAL')">
            <input type="radio" name="scopeChoice" value="GLOBAL" checked />
            <div>
              <div class="scope-title" style="color:#f59e0b;">🔒 Permanent Global Boundary</div>
              <div class="scope-desc">Permanent store policy. Applies every single week automatically until modified.</div>
            </div>
          </div>
          <div class="scope-opt" id="optScopeLocal" onclick="setScopeChoice('LOCAL')">
            <input type="radio" name="scopeChoice" value="LOCAL" />
            <div>
              <div class="scope-title" style="color:#38bdf8;">⚡ Local Boundary / Override</div>
              <div class="scope-desc">One-time operational override. Applies ONLY to the upcoming week's rota.</div>
            </div>
          </div>
        </div>

        <div class="form-grid">
          <!-- Prominent User Dropdown -->
          <div class="form-group">
            <label>👤 Select Target Team Member or Department (Dropdown):</label>
            <select id="ruleTargetSelect" class="form-control">
              <optgroup label="Store & Departments">
                <option value="ALL">🌟 Entire Store Staff (ALL)</option>
                <option value="FOH">🏢 Front of House (FOH)</option>
                <option value="Kitchen">🍳 Kitchen Department</option>
              </optgroup>
              <optgroup label="Individual Team Members" id="ruleStaffOptGroup">
                <!-- Injected dynamically -->
              </optgroup>
            </select>
          </div>

          <!-- Rule Type Dropdown -->
          <div class="form-group">
            <label>⚙️ Boundary / Condition Type:</label>
            <select id="ruleTypeSelect" class="form-control" onchange="adjustRuleFormInputs()">
              <option value="WORKS_ONLY_DAYS">🗓️ Works ONLY on Specific Days (e.g. Sundays only)</option>
              <option value="BLOCKED_DAYS">🚫 Never Works on Specific Days (Blocked Days)</option>
              <option value="LATEST_FINISH">⏰ Latest Allowed Finish Time (e.g. Cannot work past 8:00 PM)</option>
              <option value="EARLIEST_START">🌅 Earliest Allowed Start Time (e.g. No mornings before 12:00)</option>
              <option value="BLOCKED_SHIFTS">🚫 Never Works Shift Type (Never Closes / Never Mornings)</option>
              <option value="MAX_HOURS">⏱️ Weekly Hours Limit / Cap (e.g. Max 20 hours)</option>
              <option value="STATION_LOCK">🍳 Lock to Specific Station (Grill Only / FOH Only)</option>
              <option value="MAX_CONCURRENT_HEADCOUNT">👥 Department Headcount Cap (Max concurrent FOH)</option>
              <option value="MANDATORY_DAYS_OFF">🏖️ Mandatory Rest Days (Guaranteed days off)</option>
            </select>
          </div>
        </div>

        <!-- Conditional Days Picker (for WORKS_ONLY_DAYS and BLOCKED_DAYS) -->
        <div class="form-group" id="daysPickerBox" style="margin-bottom:16px;">
          <label>Select Days Applicable:</label>
          <div class="days-picker">
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Mon" /> Mon</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Tue" /> Tue</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Wed" /> Wed</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Thu" /> Thu</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Fri" /> Fri</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Sat" /> Sat</label>
            <label class="day-chk-btn"><input type="checkbox" name="ruleDays" value="Sun" checked /> Sun</label>
          </div>
        </div>

        <!-- Conditional Value Input (for Times, Hours, Counts) -->
        <div class="form-grid" id="valueInputBox" style="display:none;">
          <div class="form-group">
            <label id="ruleValueLabel">Value (Time or Number):</label>
            <input type="text" id="ruleValueInput" class="form-control" placeholder="e.g. 20:00 or 20" />
          </div>
          <div class="form-group">
            <label>Rule Description Note (Optional):</label>
            <input type="text" id="ruleDescInput" class="form-control" placeholder="e.g. Cannot work past 8 PM" />
          </div>
        </div>

        <button class="btn primary" onclick="submitCustomBoundary()">💾 Save & Enforce Boundary</button>
      </div>

      <!-- Active Rules Display -->
      <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:12px; color:#f59e0b;">
        🔒 Active Global Boundaries (Permanent Store Policies)
      </h3>
      <div class="rules-grid" id="globalRulesGrid"></div>

      <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:12px; color:#38bdf8;">
        ⚡ Active Local Boundaries (Upcoming Week Only)
      </h3>
      <div class="rules-grid" id="localRulesGrid"></div>
    </div>

    <!-- TAB 3: STAFF DIRECTORY & WAGES -->
    <div class="tab-pane" id="pane-staff">
      <div class="form-box">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
          <div>
            <h3 style="font-size:1.05rem; font-weight:800;">👥 Team Members & Wage Matrix</h3>
            <p style="font-size:0.75rem; color:var(--text-muted);">Fully dynamic: Modify hours, roles, wages, or clear staff for a new store setup.</p>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <button class="btn success" onclick="restoreDefaultStaff()">🔄 Reset to UK Food Store Template</button>
            <button class="btn danger" onclick="clearAllStaff()">🗑️ Clear All Staff (New Store Setup)</button>
          </div>
        </div>

        <!-- Quick Edit Dropdown -->
        <div class="form-group" style="margin-bottom:16px;">
          <label>✏️ Select Existing Team Member to Quick Edit:</label>
          <select id="staffEditSelect" class="form-control" onchange="loadStaffIntoForm()">
            <option value="">-- Choose team member to modify details --</option>
            <!-- Populated dynamically -->
          </select>
        </div>

        <div class="form-grid">
          <div class="form-group">
            <label>Full Name:</label>
            <input type="text" id="staffNameInput" class="form-control" placeholder="e.g. David Miller" />
          </div>
          <div class="form-group">
            <label>Role:</label>
            <select id="staffRoleInput" class="form-control">
              <option value="Team Member">Team Member</option>
              <option value="Team Leader">Team Leader</option>
              <option value="Store Trainer">Store Trainer</option>
              <option value="Assistant Manager">Assistant Manager</option>
              <option value="General Manager">General Manager</option>
            </select>
          </div>
          <div class="form-group">
            <label>Pay Classification:</label>
            <select id="staffPayTypeInput" class="form-control" onchange="togglePayInputs()">
              <option value="hourly">Hourly Paid (Variable cost on rota)</option>
              <option value="salaried">Salaried (£0.00 variable rota cost)</option>
            </select>
          </div>
          <div class="form-group" id="staffRateBox">
            <label>Hourly Wage Rate (£):</label>
            <input type="number" step="0.01" id="staffRateInput" class="form-control" value="11.44" />
          </div>
          <div class="form-group">
            <label>Manager Weekly Hours Cap:</label>
            <input type="number" id="staffCapInput" class="form-control" value="20.0" />
          </div>
          <div class="form-group">
            <label>Skills (comma separated):</label>
            <input type="text" id="staffSkillsInput" class="form-control" value="FOH, Sets, Fryers" />
          </div>
        </div>

        <button class="btn primary" onclick="saveStaffMember()">💾 Save Team Member</button>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Employee Name</th>
              <th>Role</th>
              <th>Classification</th>
              <th>Hourly Rate</th>
              <th>Weekly Cap</th>
              <th>Skills</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="staffTableBody"></tbody>
        </table>
      </div>
    </div>

    <!-- TAB 4: WEEKLY CONTROLS -->
    <div class="tab-pane" id="pane-controls">
      <div class="form-box">
        <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:14px;">⚡ Weekly Operating Controls</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>Weekly Labor Budget (£):</label>
            <input type="number" id="ctrlBudgetInput" class="form-control" value="4000.0" />
          </div>
          <div class="form-group">
            <label>Trading Strategy Mode:</label>
            <select id="ctrlModeInput" class="form-control">
              <option value="balanced">Balanced & Fair Hours Distribution</option>
              <option value="powerhouse">Month-End Pay-Weekend Powerhouse</option>
            </select>
          </div>
        </div>
        <button class="btn primary" onclick="saveWeeklyControls()">Apply & Re-Calculate Rota</button>
      </div>

      <div class="form-box">
        <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:10px;">🏖️ Staff Booked Leave / Sickness (This Week Only)</h3>
        <p style="font-size:0.75rem; color:var(--text-muted); margin-bottom:14px;">Check any team member who is unavailable or on vacation for this upcoming week.</p>
        <div id="leaveChecklistGrid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:10px;"></div>
      </div>
    </div>

    <!-- TAB 5: AI CHAT ASSISTANT -->
    <div class="tab-pane" id="pane-chat">
      <div class="chat-layout">
        <div class="chat-main">
          <div class="chat-messages" id="chatLogs"></div>

          <div class="chat-input-bar">
            <!-- Dropdown Composer Helper -->
            <div class="chat-composer-row">
              <span style="font-size:0.78rem; font-weight:700; color:#93c5fd; display:flex; align-items:center;">⚡ Quick Composer:</span>
              <select id="chatStaffSelect" class="select-styled" style="font-size:0.75rem; padding:4px 8px;">
                <!-- Populated dynamically -->
              </select>
              <select id="chatConditionSelect" class="select-styled" style="font-size:0.75rem; padding:4px 8px;">
                <option value="works only sundays">works only Sundays</option>
                <option value="works up to 8pm only">works up to 8pm only</option>
                <option value="never closes">never closes</option>
                <option value="doesn't work in mornings">doesn't work in mornings</option>
                <option value="never works on sundays and tuesdays">never works on Sundays and Tuesdays</option>
                <option value="is off this Thursday and Friday">is off this Thursday and Friday</option>
                <option value="limit to 20 hours next week">limit to 20 hours next week</option>
              </select>
              <select id="chatScopeSelect" class="select-styled" style="font-size:0.75rem; padding:4px 8px;">
                <option value="Global rule:">🔒 Global (Permanent)</option>
                <option value="This week:">⚡ Local (This week)</option>
              </select>
              <button class="btn secondary" style="padding:4px 10px; font-size:0.75rem;" onclick="applyComposerToChat()">Insert</button>
            </div>

            <!-- Free Text Row -->
            <div class="chat-text-row">
              <input type="text" id="chatInput" class="form-control" placeholder="e.g. Global rule: Wing is Lau works only sundays..." onkeydown="if(event.key==='Enter') sendChatMessage()" />
              <button class="btn primary" onclick="sendChatMessage()">Send</button>
            </div>

            <!-- Clickable Hints -->
            <div class="chat-hints">
              <span class="hint-chip" onclick="quickChat('Global rule: Taylor works only on weekends')">🔒 Taylor: Wknd Only</span>
              <span class="hint-chip" onclick="quickChat('Jordan works up to 8pm only')">🔒 Jordan: Max 8 PM</span>
              <span class="hint-chip" onclick="quickChat('Sam never closes and doesn\\'t work in mornings')">🔒 Sam: No Close/Morn</span>
              <span class="hint-chip" onclick="quickChat('Alex never works on sundays and tuesdays')">🔒 Alex: No Tue/Sun</span>
              <span class="hint-chip" onclick="quickChat('Limit FOH to 3 people max')">🔒 Global: Max 3 FOH</span>
              <span class="hint-chip" onclick="quickChat('Morgan is off this Thursday and Friday')">🏖️ Morgan: Off Thu/Fri</span>
              <span class="hint-chip" onclick="quickChat('Limit Casey to 20 hours next week')">⏱️ Casey: 20h</span>
              <span class="hint-chip" onclick="quickChat('Set labor budget to £3,800')">💰 Budget £3,800</span>
            </div>
          </div>
        </div>

        <div class="form-box" style="margin-bottom:0;">
          <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:12px;">🧠 AI Intent Compiler</h3>
          <p style="font-size:0.8rem; color:var(--text-muted); line-height:1.5; margin-bottom:14px;">
            The assistant translates everyday spoken English into mathematical CP-SAT boundaries.
          </p>
          <div style="font-size:0.78rem; color:#cbd5e1; display:flex; flex-direction:column; gap:8px;">
            <div><strong>• Global Boundaries:</strong> Type <em>'Global rule: ...'</em> to make a permanent store rule that applies to every future week.</div>
            <div><strong>• Local Boundaries:</strong> Type <em>'This week: ...'</em> or <em>'Morgan is off this Friday'</em> for temporary single-week conditions.</div>
            <div><strong>• Role & Staff Recognition:</strong> System automatically recognizes all staff names, roles (GM, AM, TL, Trainer, Crew), and day restrictions.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 6: EMERGENCY COVER -->
    <div class="tab-pane" id="pane-emergency">
      <div class="form-box">
        <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:12px;">🚨 Emergency Last-Minute Standby Assistant</h3>
        <p style="font-size:0.78rem; color:var(--text-muted); margin-bottom:14px;">
          Instant ranking of available qualified team members when someone calls in sick 2 hours before a shift.
        </p>
        <div class="form-grid">
          <div class="form-group">
            <label>Day of Sick Call:</label>
            <select id="emDay" class="form-control">
              <option value="Mon">Monday</option>
              <option value="Tue">Tuesday</option>
              <option value="Wed">Wednesday</option>
              <option value="Thu">Thursday</option>
              <option value="Fri" selected>Friday</option>
              <option value="Sat">Saturday</option>
              <option value="Sun">Sunday</option>
            </select>
          </div>
          <div class="form-group">
            <label>Station Needed:</label>
            <select id="emShift" class="form-control">
              <option value="Grill">Kitchen Grill Close (16:00 - Close)</option>
              <option value="Fryers">Kitchen Fryers Close (16:00 - Close)</option>
              <option value="Sets">Kitchen Sets Support (17:00 - 22:30)</option>
              <option value="FOH">FOH Keyholder / Till (16:00 - Close)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Who Called In Sick (Dropdown):</label>
            <select id="emAbsentSelect" class="form-control"></select>
          </div>
        </div>
        <button class="btn primary" onclick="runEmergencyLookup()">🔍 Find Top 3 Replacements</button>
      </div>

      <div id="emResultsBox" style="display:none;">
        <h3 style="font-size:1.05rem; font-weight:800; margin-bottom:12px;">Top Recommended Standby Cover:</h3>
        <div id="emCardsGrid" class="rules-grid"></div>
      </div>
    </div>

  </div>

  <script>
    let state = {{ state_json | safe }};
    let currentScopeChoice = 'GLOBAL';

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
      });
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `pane-${tabId}`);
      });

      if (tabId === 'rules') {
        populateAllStaffDropdowns();
        adjustRuleFormInputs();
        renderRulesDisplay();
      }
      if (tabId === 'staff') renderStaffTable();
      if (tabId === 'controls') renderControlsTab();
      if (tabId === 'emergency') populateEmergencyDropdown();
    }

    function setScopeChoice(scope) {
      currentScopeChoice = scope;
      document.querySelectorAll('input[name="scopeChoice"]').forEach(r => {
        r.checked = (r.value === scope);
      });
      document.getElementById('optScopeGlobal').classList.toggle('selected-global', scope === 'GLOBAL');
      document.getElementById('optScopeLocal').classList.toggle('selected-local', scope === 'LOCAL');
    }

    function populateAllStaffDropdowns() {
      const staffList = state.staff_list || [];

      // 1. Rules Target Dropdown
      const ruleOptGroup = document.getElementById('ruleStaffOptGroup');
      if (ruleOptGroup) {
        ruleOptGroup.innerHTML = '';
        staffList.forEach(w => {
          const opt = document.createElement('option');
          opt.value = w.id;
          opt.innerText = `${w.name} (${w.role} · ${w.manager_weekly_cap}h cap)`;
          ruleOptGroup.appendChild(opt);
        });
      }

      // 2. Timetable Filter Dropdown
      const ttSelect = document.getElementById('timetableStaffFilter');
      if (ttSelect) {
        const curVal = ttSelect.value;
        ttSelect.innerHTML = '<option value="ALL">👁️ View All Staff Members (Full Store View)</option>';
        staffList.forEach(w => {
          const opt = document.createElement('option');
          opt.value = w.id;
          opt.innerText = `${w.name} (${w.role})`;
          ttSelect.appendChild(opt);
        });
        ttSelect.value = curVal || 'ALL';
      }

      // 3. Chat Composer Dropdown
      const chatSelect = document.getElementById('chatStaffSelect');
      if (chatSelect) {
        chatSelect.innerHTML = '';
        staffList.forEach(w => {
          const opt = document.createElement('option');
          opt.value = w.name;
          opt.innerText = w.name;
          chatSelect.appendChild(opt);
        });
      }

      // 4. Staff Edit Dropdown
      const editSelect = document.getElementById('staffEditSelect');
      if (editSelect) {
        editSelect.innerHTML = '<option value="">-- Choose team member to modify details --</option>';
        staffList.forEach(w => {
          const opt = document.createElement('option');
          opt.value = w.id;
          opt.innerText = `${w.name} (${w.role})`;
          editSelect.appendChild(opt);
        });
      }

      // 5. Manager Quick Day Off Dropdown
      const quickStaffOff = document.getElementById('quickStaffOffSelect');
      if (quickStaffOff) {
        quickStaffOff.innerHTML = '<option value="">-- Worker --</option>';
        staffList.forEach(w => {
          const opt = document.createElement('option');
          opt.value = w.id;
          opt.innerText = w.name;
          quickStaffOff.appendChild(opt);
        });
      }
    }

    function adjustRuleFormInputs() {
      const type = document.getElementById('ruleTypeSelect').value;
      const daysBox = document.getElementById('daysPickerBox');
      const valBox = document.getElementById('valueInputBox');
      const valLbl = document.getElementById('ruleValueLabel');
      const valInput = document.getElementById('ruleValueInput');

      if (type === 'WORKS_ONLY_DAYS' || type === 'BLOCKED_DAYS') {
        daysBox.style.display = 'block';
        valBox.style.display = 'none';
      } else if (type === 'LATEST_FINISH' || type === 'EARLIEST_START') {
        // Show BOTH Days Picker and Time input so manager can set person timings for specific days
        daysBox.style.display = 'block';
        valBox.style.display = 'grid';
        if (type === 'LATEST_FINISH') {
          valLbl.innerText = 'Latest Allowed Finish Time (e.g. 18:00 or 20:00):';
          valInput.placeholder = '18:00';
        } else {
          valLbl.innerText = 'Earliest Allowed Start Time (e.g. 12:00 or 14:00):';
          valInput.placeholder = '14:00';
        }
      } else {
        daysBox.style.display = 'none';
        valBox.style.display = 'grid';

        if (type === 'BLOCKED_SHIFTS') {
          valLbl.innerText = 'Blocked Shift Type (Close or Morning):';
          valInput.placeholder = 'Close, Morning';
        } else if (type === 'MAX_HOURS') {
          valLbl.innerText = 'Weekly Hours Limit (Hours):';
          valInput.placeholder = '20.0';
        } else if (type === 'STATION_LOCK') {
          valLbl.innerText = 'Dedicated Station (Grill or FOH):';
          valInput.placeholder = 'Grill';
        } else if (type === 'MAX_CONCURRENT_HEADCOUNT') {
          valLbl.innerText = 'Max Concurrent Staff Count:';
          valInput.placeholder = '3';
        } else if (type === 'MANDATORY_DAYS_OFF') {
          valLbl.innerText = 'Guaranteed Rest Days per Week:';
          valInput.placeholder = '2';
        } else {
          valLbl.innerText = 'Value:';
          valInput.placeholder = '';
        }
      }
    }

    async function submitCustomBoundary() {
      const scope = currentScopeChoice;
      const target = document.getElementById('ruleTargetSelect').value;
      const type = document.getElementById('ruleTypeSelect').value;
      const checkedDays = Array.from(document.querySelectorAll('input[name="ruleDays"]:checked')).map(cb => cb.value);
      const targetName = document.getElementById('ruleTargetSelect').selectedOptions[0].text;
      let val = null;
      let desc = '';
      let days = [];

      if (type === 'WORKS_ONLY_DAYS' || type === 'BLOCKED_DAYS') {
        if (checkedDays.length === 0) return alert('Please check at least one day!');
        val = checkedDays;
        desc = `${targetName} ${type === 'WORKS_ONLY_DAYS' ? 'works ONLY on' : 'BLOCKED on'} ${checkedDays.join(', ')}.`;
      } else if (type === 'LATEST_FINISH' || type === 'EARLIEST_START') {
        val = document.getElementById('ruleValueInput').value.trim();
        if (!val) return alert('Please enter a time value (e.g. 18:00 or 20:00)!');
        days = (checkedDays.length > 0 && checkedDays.length < 7) ? checkedDays : [];
        const dayNote = days.length > 0 ? ` on ${days.join(', ')}` : '';
        const customDesc = document.getElementById('ruleDescInput').value.trim();
        desc = customDesc || `${targetName} ${type === 'LATEST_FINISH' ? 'latest finish is ' : 'earliest start is '}${val}${dayNote}.`;
      } else {
        val = document.getElementById('ruleValueInput').value.trim();
        if (!val) return alert('Please provide a value for this condition!');
        const customDesc = document.getElementById('ruleDescInput').value.trim();
        desc = customDesc || `${type.replace(/_/g, ' ')} of ${val} applied to ${targetName}.`;
        if (!isNaN(val) && val !== '' && !val.includes(':')) val = parseFloat(val);
      }

      const newRule = {
        id: `rule_${scope.toLowerCase()}_${Date.now()}`,
        scope: scope,
        target_type: (target === 'FOH' || target === 'Kitchen') ? 'DEPARTMENT' : (target === 'ALL' ? 'STORE' : 'EMPLOYEE'),
        target_id: target,
        rule_type: type,
        days: days,
        value: val,
        description: desc
      };

      try {
        const res = await fetch('/api/add_rule', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ rule: newRule })
        });
        const data = await res.json();
        state = data.state;
        renderRulesDisplay();
        renderUI();
        alert(`✅ ${scope} Boundary saved and enforced on live rota!`);
      } catch (err) {
        console.error(err);
      }
    }

    async function deleteRule(ruleId, scope) {
      if (!confirm(`Remove this ${scope} boundary? The rota will immediately re-calculate without it.`)) return;
      try {
        const res = await fetch('/api/delete_rule', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ rule_id: ruleId, scope: scope })
        });
        const data = await res.json();
        state = data.state;
        renderRulesDisplay();
        renderUI();
      } catch (err) {
        console.error(err);
      }
    }

    function renderRulesDisplay() {
      // Global Rules
      const gGrid = document.getElementById('globalRulesGrid');
      gGrid.innerHTML = '';
      const globals = state.global_rules || [];
      if (globals.length === 0) {
        gGrid.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding:12px;">No global boundaries configured.</div>';
      } else {
        globals.forEach(r => {
          const card = document.createElement('div');
          card.className = 'rule-card global';
          card.innerHTML = `
            <div>
              <div class="rule-head">
                <span class="rule-type-badge">🔒 ${r.rule_type}</span>
                <button class="btn danger" style="padding: 2px 7px; font-size: 0.7rem;" onclick="deleteRule('${r.id}', 'GLOBAL')">Delete</button>
              </div>
              <div class="rule-desc" style="margin-top:6px;">${r.description}</div>
            </div>
            <div class="rule-meta">
              <span>Target: <strong>${r.target_id}</strong></span>
              <span>Value: <strong>${Array.isArray(r.value) ? r.value.join(', ') : r.value}</strong></span>
            </div>
          `;
          gGrid.appendChild(card);
        });
      }

      // Local Rules
      const lGrid = document.getElementById('localRulesGrid');
      lGrid.innerHTML = '';
      const locals = state.local_rules || [];
      if (locals.length === 0) {
        lGrid.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding:12px;">No weekly local boundaries configured for this week.</div>';
      } else {
        locals.forEach(r => {
          const card = document.createElement('div');
          card.className = 'rule-card local';
          card.innerHTML = `
            <div>
              <div class="rule-head">
                <span class="rule-type-badge">⚡ ${r.rule_type} (This Week)</span>
                <button class="btn danger" style="padding: 2px 7px; font-size: 0.7rem;" onclick="deleteRule('${r.id}', 'LOCAL')">Delete</button>
              </div>
              <div class="rule-desc" style="margin-top:6px;">${r.description}</div>
            </div>
            <div class="rule-meta">
              <span>Target: <strong>${r.target_id}</strong></span>
              <span>Value: <strong>${Array.isArray(r.value) ? r.value.join(', ') : r.value}</strong></span>
            </div>
          `;
          lGrid.appendChild(card);
        });
      }

      // Badges
      const totalRules = globals.length + locals.length;
      document.getElementById('rulesBadge').innerText = totalRules;
      document.getElementById('kpiRules').innerText = totalRules;
      document.getElementById('kpiRulesBreakdown').innerText = `${globals.length} Global · ${locals.length} Local`;
    }

    function renderUI() {
      populateAllStaffDropdowns();
      const roster = state.current_roster || {};
      const totalHours = roster.total_hours || 0;
      const totalCost = roster.variable_payroll || 0;
      const budget = roster.weekly_budget || state.weekly_budget || 4000;
      const variance = budget - totalCost;

      document.getElementById('kpiHours').innerText = `${totalHours}h`;
      document.getElementById('kpiSpend').innerText = `£${totalCost.toLocaleString('en-GB', {minimumFractionDigits: 2})}`;
      document.getElementById('kpiBudget').innerText = `£${budget.toLocaleString('en-GB', {minimumFractionDigits: 2})}`;
      
      const varEl = document.getElementById('kpiVariance');
      varEl.innerText = `${variance >= 0 ? '+' : ''}£${variance.toLocaleString('en-GB', {minimumFractionDigits: 2})} remaining`;
      varEl.style.color = (variance >= 0) ? '#10b981' : '#f59e0b';

      document.getElementById('staffBadge').innerText = (state.staff_list || []).length;

      // Render Timetable
      renderTimetableGrid();

      // Render Chat Logs
      renderChatLogs();

      // Rules Count
      renderRulesDisplay();
    }

    function renderTimetableGrid() {
      const grid = document.getElementById('timetableGrid');
      grid.innerHTML = '';
      const roster = state.current_roster || {};
      const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
      const dayNamesFull = {
        "Mon": "Monday (Stock Order)",
        "Tue": "Tuesday",
        "Wed": "Wednesday",
        "Thu": "Thursday",
        "Fri": "Friday (Peak Close)",
        "Sat": "Saturday (Peak Close)",
        "Sun": "Sunday"
      };

      days.forEach(day => {
        const shifts = (roster.roster && roster.roster[day]) ? roster.roster[day] : [];
        const dayHours = shifts.reduce((sum, s) => sum + s.paid_hours, 0);

        const col = document.createElement('div');
        col.className = 'day-col';

        let shiftsHtml = '';
        shifts.forEach(s => {
          let rolePillClass = 'pill foh';
          const descLower = s.desc.toLowerCase();
          if (descLower.includes('grill') || descLower.includes('fryer') || descLower.includes('prep') || descLower.includes('line')) {
            rolePillClass = 'pill kitchen';
          }
          if (s.role.includes('Manager') || s.role.includes('Leader')) {
            rolePillClass = 'pill mgmt';
          }
          if (s.is_salaried) {
            rolePillClass = 'pill salaried';
          }

          let costStr = s.is_salaried ? '<span style="color:#34d399; font-weight:700;">Salaried (£0.00)</span>' : `£${s.cost ? s.cost.toFixed(2) : (s.paid_hours * 11.44).toFixed(2)}`;

          shiftsHtml += `
            <div class="shift-card" data-worker="${s.assigned_to}">
              <div class="shift-top">
                <span>${s.time}</span>
                <span class="${rolePillClass}">${s.paid_hours}h</span>
              </div>
              <div class="shift-emp-name">${s.assigned_to}</div>
              <div class="shift-role-desc">
                <span>${s.desc}</span>
              </div>
              <div class="shift-foot">
                <span>${s.role}</span>
                <span>${costStr}</span>
              </div>
            </div>
          `;
        });

        col.innerHTML = `
          <div class="day-header">
            <span class="day-title">${dayNamesFull[day] || day}</span>
            <span class="day-stats">${shifts.length} shifts · ${dayHours.toFixed(1)}h</span>
          </div>
          <div class="shifts-stack">
            ${shiftsHtml || '<div style="color:var(--text-muted); font-size:0.8rem; text-align:center; padding:30px;">No shifts</div>'}
          </div>
        `;
        grid.appendChild(col);
      });

      applyStaffHighlight();
    }

    function applyStaffHighlight() {
      const selectedId = document.getElementById('timetableStaffFilter').value;
      const cards = document.querySelectorAll('.shift-card');
      const summaryBox = document.getElementById('highlightSummary');

      if (!selectedId || selectedId === 'ALL') {
        cards.forEach(c => {
          c.classList.remove('highlighted');
          c.classList.remove('dimmed');
        });
        summaryBox.innerText = '';
        return;
      }

      // Find selected worker
      const worker = (state.staff_list || []).find(w => w.id === selectedId);
      const targetName = worker ? worker.name : selectedId;

      let matchCount = 0;
      let matchHours = 0;

      cards.forEach(c => {
        const workerAttr = c.getAttribute('data-worker');
        if (workerAttr === targetName) {
          c.classList.add('highlighted');
          c.classList.remove('dimmed');
          matchCount++;
          // extract hours
          const hMatch = c.querySelector('.pill').innerText;
          matchHours += parseFloat(hMatch) || 0;
        } else {
          c.classList.remove('highlighted');
          c.classList.add('dimmed');
        }
      });

      const roster = state.current_roster || {};
      const daysOff = (roster.days_off && roster.days_off[targetName]) ? roster.days_off[targetName] : [];

      summaryBox.innerText = `✨ Highlighted ${targetName}: ${matchCount} Shifts (${matchHours.toFixed(1)}h) · Rest Days: ${daysOff.join(', ') || 'None'}`;
    }

    function renderChatLogs() {
      const logs = document.getElementById('chatLogs');
      logs.innerHTML = '';
      (state.chat_history || []).forEach(msg => {
        const div = document.createElement('div');
        div.className = `msg-bubble ${msg.sender}`;
        let formatted = msg.text
          .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
          .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
          .replace(/\\n/g, '<br>');
        div.innerHTML = formatted;
        logs.appendChild(div);
      });
      logs.scrollTop = logs.scrollHeight;
    }

    function applyComposerToChat() {
      const worker = document.getElementById('chatStaffSelect').value;
      const cond = document.getElementById('chatConditionSelect').value;
      const scopePrefix = document.getElementById('chatScopeSelect').value;
      document.getElementById('chatInput').value = `${scopePrefix} ${worker} ${cond}`;
      sendChatMessage();
    }

    async function sendChatMessage() {
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      state.chat_history.push({ sender: 'user', text: text });
      renderChatLogs();

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        state = data.state;
        renderUI();
      } catch (err) {
        console.error(err);
      }
    }

    function quickChat(txt) {
      document.getElementById('chatInput').value = txt;
      sendChatMessage();
    }

    function executeQuickCommand() {
      const input = document.getElementById('quickCommandInput');
      const text = input ? input.value.trim() : '';
      if (!text) return;
      input.value = '';
      quickChat(text);
    }

    function quickMarkOff() {
      const staffSelect = document.getElementById('quickStaffOffSelect');
      const daySelect = document.getElementById('quickDayOffSelect');
      if (!staffSelect || !staffSelect.value) {
        alert('Please select a team member from the dropdown first.');
        return;
      }
      const staffName = staffSelect.options[staffSelect.selectedIndex].text;
      const day = daySelect ? daySelect.value : 'Mon';
      quickChat(`${staffName} is off this ${day}`);
    }

    async function regenerateRota(mode) {
      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: mode })
        });
        const data = await res.json();
        state = data.state;
        renderUI();
      } catch (err) {
        console.error(err);
      }
    }

    function renderStaffTable() {
      const tbody = document.getElementById('staffTableBody');
      tbody.innerHTML = '';
      (state.staff_list || []).forEach(w => {
        const tr = document.createElement('tr');
        const payStr = w.is_salaried ? '<span class="pill salaried">Salaried (£0.00)</span>' : `£${w.hourly_rate ? w.hourly_rate.toFixed(2) : '11.44'}/hr`;
        tr.innerHTML = `
          <td><strong>${w.name}</strong></td>
          <td>${w.role}</td>
          <td>${w.is_salaried ? 'Salaried Store Manager' : 'Hourly Team Member'}</td>
          <td>${payStr}</td>
          <td>${w.manager_weekly_cap} hrs</td>
          <td>${(w.skills || []).join(', ')}</td>
          <td><button class="btn danger" style="padding: 2px 7px; font-size:0.7rem;" onclick="removeStaffMember('${w.id}')">Remove</button></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function loadStaffIntoForm() {
      const selectedId = document.getElementById('staffEditSelect').value;
      if (!selectedId) return;
      const worker = (state.staff_list || []).find(w => w.id === selectedId);
      if (!worker) return;

      document.getElementById('staffNameInput').value = worker.name;
      document.getElementById('staffRoleInput').value = worker.role;
      document.getElementById('staffPayTypeInput').value = worker.is_salaried ? 'salaried' : 'hourly';
      document.getElementById('staffRateInput').value = worker.hourly_rate || 11.44;
      document.getElementById('staffCapInput').value = worker.manager_weekly_cap || 20.0;
      document.getElementById('staffSkillsInput').value = (worker.skills || []).join(', ');
      togglePayInputs();
    }

    function togglePayInputs() {
      const isSal = document.getElementById('staffPayTypeInput').value === 'salaried';
      document.getElementById('staffRateBox').style.opacity = isSal ? '0.3' : '1.0';
    }

    async function saveStaffMember() {
      const name = document.getElementById('staffNameInput').value.trim();
      if (!name) return alert('Please enter a team member name');
      const role = document.getElementById('staffRoleInput').value;
      const isSal = document.getElementById('staffPayTypeInput').value === 'salaried';
      const rate = isSal ? 0.0 : parseFloat(document.getElementById('staffRateInput').value);
      const cap = parseFloat(document.getElementById('staffCapInput').value) || 20.0;
      const skillsStr = document.getElementById('staffSkillsInput').value;
      const skills = skillsStr ? skillsStr.split(',').map(s => s.trim()) : ["FOH", "Sets", "Fryers"];

      const sid = name.toLowerCase().replace(/\\s+/g, '_');
      const idx = (state.staff_list || []).findIndex(w => w.id === sid);

      const workerObj = {
        id: sid,
        name: name,
        role: role,
        is_salaried: isSal,
        hourly_rate: rate,
        manager_weekly_cap: cap,
        max_weekly_hours: cap + 5,
        skills: skills,
        is_keyholder: role.includes('Manager') || role.includes('Leader') || role.includes('Trainer'),
        primary_dept: skills.includes('Grill') ? 'Kitchen' : 'FOH',
        availability: 'Any'
      };

      if (idx >= 0) {
        state.staff_list[idx] = workerObj;
      } else {
        state.staff_list.push(workerObj);
      }

      try {
        const res = await fetch('/api/save_staff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ staff_list: state.staff_list })
        });
        const data = await res.json();
        state = data.state;
        renderStaffTable();
        renderUI();
        alert(`Saved ${name} successfully!`);
      } catch (err) {
        console.error(err);
      }
    }

    async function removeStaffMember(id) {
      if (!confirm('Remove this team member from the store?')) return;
      state.staff_list = state.staff_list.filter(w => w.id !== id);
      try {
        const res = await fetch('/api/save_staff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ staff_list: state.staff_list })
        });
        const data = await res.json();
        state = data.state;
        renderStaffTable();
        renderUI();
      } catch (err) {
        console.error(err);
      }
    }

    async function clearAllStaff() {
      if (!confirm('Warning: This will clear the current staff list so you can setup a new store team. Proceed?')) return;
      state.staff_list = [];
      try {
        const res = await fetch('/api/save_staff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ staff_list: [] })
        });
        const data = await res.json();
        state = data.state;
        renderStaffTable();
        renderUI();
      } catch (err) {
        console.error(err);
      }
    }

    async function restoreDefaultStaff() {
      if (!confirm('Reset team directory to the standard UK Food Store template?')) return;
      try {
        const res = await fetch('/api/restore_default_staff', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
        });
        const data = await res.json();
        state = data.state;
        renderStaffTable();
        renderUI();
        alert('✅ Restored standard UK Food Store team template successfully!');
      } catch (err) {
        console.error(err);
      }
    }

    function renderControlsTab() {
      document.getElementById('ctrlBudgetInput').value = state.weekly_budget || 4000;
      document.getElementById('ctrlModeInput').value = state.mode || 'balanced';

      const leaveBox = document.getElementById('leaveChecklistGrid');
      leaveBox.innerHTML = '';
      (state.staff_list || []).forEach(w => {
        const isOff = (state.leave && state.leave[w.id]);
        const div = document.createElement('div');
        div.style.background = '#0d1527';
        div.style.padding = '8px 12px';
        div.style.borderRadius = '6px';
        div.style.border = '1px solid #1e293b';
        div.style.fontSize = '0.82rem';
        div.innerHTML = `
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="leave_${w.id}" ${isOff ? 'checked' : ''} onchange="toggleLeaveWorker('${w.id}')" />
            <span>${w.name} (${w.role})</span>
          </label>
        `;
        leaveBox.appendChild(div);
      });
    }

    function toggleLeaveWorker(wid) {
      if (!state.leave) state.leave = {};
      const chk = document.getElementById(`leave_${wid}`).checked;
      if (chk) {
        state.leave[wid] = "All";
      } else {
        delete state.leave[wid];
      }
    }

    async function saveWeeklyControls() {
      const budget = parseFloat(document.getElementById('ctrlBudgetInput').value);
      const mode = document.getElementById('ctrlModeInput').value;
      state.weekly_budget = budget;
      state.mode = mode;
      state.is_pay_week = (mode === 'powerhouse');

      try {
        const res = await fetch('/api/save_local', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(state)
        });
        const data = await res.json();
        state = data.state;
        renderUI();
        switchTab('timetable');
      } catch (err) {
        console.error(err);
      }
    }

    function populateEmergencyDropdown() {
      const select = document.getElementById('emAbsentSelect');
      select.innerHTML = '';
      (state.staff_list || []).forEach(w => {
        const opt = document.createElement('option');
        opt.value = w.id;
        opt.innerText = `${w.name} (${w.role})`;
        select.appendChild(opt);
      });
    }

    async function runEmergencyLookup() {
      const day = document.getElementById('emDay').value;
      const shift = document.getElementById('emShift').value;
      const absentId = document.getElementById('emAbsentSelect').value;

      try {
        const res = await fetch('/api/emergency_lookup', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ day: day, shift: shift, absent_id: absentId })
        });
        const data = await res.json();
        const resultsBox = document.getElementById('emResultsBox');
        const cardsGrid = document.getElementById('emCardsGrid');
        cardsGrid.innerHTML = '';

        if (!data.candidates || data.candidates.length === 0) {
          cardsGrid.innerHTML = '<div style="color:var(--text-muted); padding:16px;">No standby cover found for this station.</div>';
        } else {
          data.candidates.forEach((c, idx) => {
            const card = document.createElement('div');
            card.className = 'rule-card local';
            card.innerHTML = `
              <div>
                <div class="rule-head">
                  <span style="font-weight:800; color:#38bdf8;">#${idx+1} Recommendation: ${c.name}</span>
                  <span class="pill mgmt">Score: ${c.score}</span>
                </div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin: 6px 0;">Role: ${c.role} | Cap: ${c.manager_cap}h</div>
                <div style="font-size:0.78rem; color:#e2e8f0;">
                  ${c.reasons.map(r => `<div>✓ ${r}</div>`).join('')}
                </div>
              </div>
            `;
            cardsGrid.appendChild(card);
          });
        }
        resultsBox.style.display = 'block';
      } catch (err) {
        console.error(err);
      }
    }

    // Initial Execution
    populateAllStaffDropdowns();
    renderUI();

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(err => console.log('SW registration note:', err));
      });
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, state_json=json.dumps(CURRENT_STATE))

@app.route("/manifest.json")
def manifest():
    manifest_data = {
        "name": "UK Food Store Rota Optimizer",
        "short_name": "UK Rota",
        "description": "Store Rota & Staff Scheduling System with AI Optimization",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#090d16",
        "theme_color": "#0d1322",
        "orientation": "any",
        "icons": [
            {
                "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%233b82f6'/><text x='50%' y='55%' font-size='50' font-weight='800' fill='white' dominant-baseline='middle' text-anchor='middle'>UK</text></svg>",
                "sizes": "192x192 512x512",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    return Response(json.dumps(manifest_data), mimetype="application/manifest+json")

@app.route("/sw.js")
def service_worker():
    sw_code = """
    self.addEventListener('install', e => {
      self.skipWaiting();
    });
    self.addEventListener('activate', e => {
      e.waitUntil(clients.claim());
    });
    self.addEventListener('fetch', e => {
      e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    });
    """
    return Response(sw_code, mimetype="application/javascript")

@app.route("/api/state")
def get_state():
    return jsonify(CURRENT_STATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_msg = data.get("message", "")
    
    reply, new_state, should_regen = chat_parser.parse_user_message(user_msg, CURRENT_STATE)
    new_state["chat_history"].append({"sender": "bot", "text": reply})
    
    if should_regen:
        combined_rules = list(new_state.get("global_rules", [])) + list(new_state.get("local_rules", []))
        res = dynamic_solver.solve_universal_rota(
            staff_list=new_state.get("staff_list", []),
            store_hours=new_state.get("store_hours", {}),
            global_rules=combined_rules,
            weekly_rules=new_state,
            mode=new_state.get("mode", "balanced"),
            is_pay_week=new_state.get("is_pay_week", False),
            weekly_budget=new_state.get("weekly_budget", 4000.0)
        )
        new_state["current_roster"] = res
        
    save_state(new_state)
    return jsonify({"reply": reply, "state": new_state})

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json or {}
    mode = data.get("mode", "balanced")
    is_pay = (mode == "powerhouse")
    
    CURRENT_STATE["mode"] = mode
    CURRENT_STATE["is_pay_week"] = is_pay
    
    combined_rules = list(CURRENT_STATE.get("global_rules", [])) + list(CURRENT_STATE.get("local_rules", []))
    res = dynamic_solver.solve_universal_rota(
        staff_list=CURRENT_STATE.get("staff_list", []),
        store_hours=CURRENT_STATE.get("store_hours", {}),
        global_rules=combined_rules,
        weekly_rules=CURRENT_STATE,
        mode=mode,
        is_pay_week=is_pay,
        weekly_budget=CURRENT_STATE.get("weekly_budget", 4000.0)
    )
    CURRENT_STATE["current_roster"] = res
    CURRENT_STATE["chat_history"].append({
        "sender": "bot",
        "text": f"⚡ Generated **{mode.title()} Rota** ({res.get('total_hours')} hours | Variable Spend: £{res.get('variable_payroll', 0):,.2f})."
    })
    save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE})

@app.route("/api/save_local", methods=["POST"])
def save_local():
    data = request.json or {}
    CURRENT_STATE["weekly_budget"] = data.get("weekly_budget", 4000.0)
    CURRENT_STATE["mode"] = data.get("mode", "balanced")
    CURRENT_STATE["is_pay_week"] = (CURRENT_STATE["mode"] == "powerhouse")
    CURRENT_STATE["leave"] = data.get("leave", {})
    
    res = solve_current()
    CURRENT_STATE["current_roster"] = res
    save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE})

@app.route("/api/save_staff", methods=["POST"])
def save_staff():
    data = request.json or {}
    CURRENT_STATE["staff_list"] = data.get("staff_list", [])
    
    res = solve_current()
    CURRENT_STATE["current_roster"] = res
    save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE})

@app.route("/api/restore_default_staff", methods=["POST"])
def restore_default_staff():
    import copy
    staff = copy.deepcopy(rota_engine.DEFAULT_STAFF)
    for s in staff:
        if s.get("is_salaried") or s.get("salaried"):
            s["manager_weekly_cap"] = s.get("contract_hours", 45.0)
            s["max_weekly_hours"] = s.get("contract_hours", 45.0)
    CURRENT_STATE["staff_list"] = staff
    res = solve_current()
    CURRENT_STATE["current_roster"] = res
    save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE, "message": "Restored UK Food Store sample template successfully!"})

@app.route("/api/add_rule", methods=["POST"])
def add_rule():
    data = request.json or {}
    rule = data.get("rule")
    if rule:
        scope = rule.get("scope", "GLOBAL")
        if scope == "GLOBAL":
            CURRENT_STATE["global_rules"].append(rule)
        else:
            CURRENT_STATE["local_rules"].append(rule)
            
        res = solve_current()
        CURRENT_STATE["current_roster"] = res
        save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE})

@app.route("/api/delete_rule", methods=["POST"])
def delete_rule():
    data = request.json or {}
    rule_id = data.get("rule_id")
    scope = data.get("scope", "GLOBAL")
    
    if rule_id:
        if scope == "GLOBAL":
            CURRENT_STATE["global_rules"] = [r for r in CURRENT_STATE["global_rules"] if r.get("id") != rule_id]
        else:
            CURRENT_STATE["local_rules"] = [r for r in CURRENT_STATE["local_rules"] if r.get("id") != rule_id]
            
        res = solve_current()
        CURRENT_STATE["current_roster"] = res
        save_state(CURRENT_STATE)
    return jsonify({"state": CURRENT_STATE})

@app.route("/api/emergency_lookup", methods=["POST"])
def emergency_lookup():
    data = request.json or {}
    day = data.get("day", "Fri")
    shift = data.get("shift", "Grill")
    absent_id = data.get("absent_id", "")
    
    candidates = []
    already_working = set()
    roster = CURRENT_STATE.get("current_roster", {}).get("roster", {})
    for s in roster.get(day, []):
        for w in CURRENT_STATE.get("staff_list", []):
            if w["name"] == s["assigned_to"]:
                already_working.add(w["id"])

    for w in CURRENT_STATE.get("staff_list", []):
        if (absent_id and w["id"] == absent_id) or w["id"] in already_working:
            continue
        has_skill = (shift in w.get("skills", [])) or (w.get("role") in ["General Manager", "Assistant Manager", "Team Leader", "Store Manager"])
        if not has_skill:
            continue

        score = 100
        reasons = []
        if w.get("emergency_standby"):
            score += 50
            reasons.append("Dedicated standby on file")
        if len(w.get("skills", [])) >= 3:
            score += 30
            reasons.append(f"Versatile all-rounder (covers {shift})")
        if shift == "Grill" and "Grill" in w.get("skills", []) and w.get("role") in ["Store Trainer", "Team Leader"]:
            score += 40
            reasons.append("Senior Line Specialist")

        candidates.append({
            "name": w["name"],
            "role": w["role"],
            "manager_cap": w.get("manager_weekly_cap", 20.0),
            "score": score,
            "reasons": reasons or ["Certified on station"]
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return jsonify({"candidates": candidates[:3]})

@app.route("/api/export_csv")
def export_csv():
    roster = CURRENT_STATE.get("current_roster", {}).get("roster", {})
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Day", "Shift Time", "Paid Hours", "Role", "Assigned Staff", "Station Task", "Hourly Rate (£)", "Shift Cost (£)"])
    
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        shifts = roster.get(day, [])
        for s in shifts:
            writer.writerow([
                day,
                s.get("time", ""),
                s.get("paid_hours", 0),
                s.get("role", ""),
                s.get("assigned_to", ""),
                s.get("desc", ""),
                "Salaried (£0.00)" if s.get("is_salaried") else f"£{s.get('hourly_rate', 11.44):.2f}",
                "£0.00" if s.get("is_salaried") else f"£{s.get('cost', 0):.2f}"
            ])
            
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=store_rota.csv"}
    )

if __name__ == "__main__":
    port = 5055
    print(f"Starting Universal Store Rota Manager V7 at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
