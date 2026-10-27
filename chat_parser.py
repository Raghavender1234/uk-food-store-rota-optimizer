"""
UK Food Store Rota Optimizer - Universal Dynamic Natural Language Parser
Converts any manager request into structured Global or Local Boundaries.
100% Dynamic - Learns employee names directly from the active staff list.
Supports day-specific timing constraints (e.g. "On Fridays Jordan works up to 6pm only").
"""

import re
from typing import Dict, Any, Tuple, List, Optional

DAY_PATTERNS = {
    'Mon': r'\b(?:mon|monday|mondays)\b',
    'Tue': r'\b(?:tue|tues|tuesday|tuesdays)\b',
    'Wed': r'\b(?:wed|wednesday|wednesdays)\b',
    'Thu': r'\b(?:thu|thur|thurs|thursday|thursdays)\b',
    'Fri': r'\b(?:fri|friday|fridays)\b',
    'Sat': r'\b(?:sat|saturday|saturdays)\b',
    'Sun': r'\b(?:sun|sunday|sundays)\b',
}

ROLE_ALIASES = {
    "gm": ["General Manager", "Store Manager"],
    "general manager": ["General Manager"],
    "store manager": ["Store Manager", "General Manager"],
    "am": ["Assistant Manager"],
    "assistant manager": ["Assistant Manager"],
    "tl": ["Team Leader", "Shift Supervisor"],
    "team leader": ["Team Leader"],
    "supervisor": ["Shift Supervisor", "Team Leader"],
    "trainer": ["Store Trainer"],
    "store trainer": ["Store Trainer"]
}

def resolve_staff(text: str, staff_list: List[Dict[str, Any]]) -> Optional[Tuple[str, str]]:
    """
    Finds a staff member mentioned in the text using the dynamic staff_list and alias mappings.
    Returns: (staff_id, staff_display_name) or None
    """
    lower = text.lower()

    # 1. Check full names and specific staff aliases from active staff_list
    for s in staff_list:
        full_name = s.get("name", "").lower()
        sid = s.get("id", "")
        
        # Check custom aliases if defined on staff profile
        for custom_alias in s.get("aliases", []):
            if re.search(r'\b' + re.escape(custom_alias.lower()) + r'\b', lower):
                return sid, s.get("name")

        # Exact full name match
        if full_name and re.search(r'\b' + re.escape(full_name) + r'\b', lower):
            return sid, s.get("name")

        # First name match (minimum 3 chars to prevent collisions)
        parts = full_name.split()
        if parts:
            first = parts[0]
            if len(first) >= 3 and re.search(r'\b' + re.escape(first) + r'\b', lower):
                return sid, s.get("name")
            if len(parts) > 1:
                last = parts[-1]
                if len(last) >= 3 and re.search(r'\b' + re.escape(last) + r'\b', lower):
                    return sid, s.get("name")

        # ID match
        if sid and (re.search(r'\b' + re.escape(sid.replace("_", " ")) + r'\b', lower) or re.search(r'\b' + re.escape(sid) + r'\b', lower)):
            return sid, s.get("name")

    # 2. Check role shortcuts (e.g. "gm is off on Monday", "assign am to open")
    for role_alias, target_roles in ROLE_ALIASES.items():
        pattern = r'\b' + re.escape(role_alias) + r'\b'
        if re.search(pattern, lower):
            match = next((s for s in staff_list if s.get("role") in target_roles), None)
            if match:
                return match["id"], match["name"]

    return None

def extract_days(text: str) -> List[str]:
    """Extracts unique days of the week in chronological order."""
    lower = text.lower()
    days = []
    for code, pat in DAY_PATTERNS.items():
        if re.search(pat, lower):
            days.append(code)
    week_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return sorted(days, key=lambda d: week_order.index(d) if d in week_order else 99)

def extract_time_str(text: str) -> Optional[str]:
    """Extracts time string and converts to 24h format HH:MM."""
    lower = text.lower()
    t_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', lower)
    if not t_match:
        return None
    raw_t = t_match.group(1).strip()
    
    if ":" in raw_t:
        parts = raw_t.split(":")
        h = int(re.search(r'\d+', parts[0]).group())
        m = int(re.search(r'\d+', parts[1]).group())
        if "pm" in raw_t and h < 12:
            h += 12
        elif "am" in raw_t and h == 12:
            h = 0
        return f"{h:02d}:{m:02d}"
    else:
        h = int(re.search(r'\d+', raw_t).group())
        if "pm" in raw_t and h < 12:
            h += 12
        elif "am" in raw_t and h == 12:
            h = 0
        elif h <= 12 and any(p in lower for p in ["evening", "afternoon", "close", "night", "dinner"]):
            if h < 12:
                h += 12
        return f"{h:02d}:00"

def parse_user_message(text: str, current_state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
    """
    Parses user message and updates state.
    Returns: (response_message, updated_state, should_regenerate_rota)
    """
    raw = text.strip()
    lower = raw.lower()
    state = current_state

    if "global_rules" not in state:
        state["global_rules"] = []
    if "local_rules" not in state:
        state["local_rules"] = []
    if "leave" not in state:
        state["leave"] = {}
    if "cap_overrides" not in state:
        state["cap_overrides"] = {}
    if "add_staff" not in state:
        state["add_staff"] = []
    if "staff_list" not in state:
        state["staff_list"] = []

    staff_list = state.get("staff_list", [])

    is_explicit_global = any(kw in lower for kw in ["global", "permanent", "always", "every week", "store rule", "forever"])
    is_explicit_local = any(kw in lower for kw in ["local", "this week", "next week", "coming week", "temporary", "temp", "only for next week"])
    
    scope = "GLOBAL" if is_explicit_global else ("LOCAL" if is_explicit_local else None)

    # 1. FOH / KITCHEN DEPARTMENT HEADCOUNT CAP
    foh_match = re.search(r'(?:limit|max|cap)\s+(?:the\s+)?(foh|front|kitchen)\s+(?:staff\s+)?to\s+(\d+)', lower)
    if foh_match:
        dept_raw = foh_match.group(1)
        dept = "Kitchen" if "kitchen" in dept_raw else "FOH"
        limit_n = int(foh_match.group(2))
        chosen_scope = scope or "GLOBAL"
        new_rule = {
            "id": f"rule_{chosen_scope.lower()}_{dept.lower()}_headcount_{len(state['global_rules'])+len(state['local_rules'])+1}",
            "scope": chosen_scope,
            "target_type": "DEPARTMENT",
            "target_id": dept,
            "rule_type": "MAX_CONCURRENT_HEADCOUNT",
            "dept": dept,
            "value": limit_n,
            "description": f"Limit {dept} staff to maximum {limit_n} people concurrently on shift."
        }
        target_list = state["global_rules"] if chosen_scope == "GLOBAL" else state["local_rules"]
        target_list.append(new_rule)
        badge = "🔒 Global Boundary (Permanent)" if chosen_scope == "GLOBAL" else "⚡ Local Boundary (This Week Only)"
        return f"{badge}: **{new_rule['description']}** has been enforced. Re-optimizing rota...", state, True

    # 2. LABOR BUDGET COMMAND
    budget_match = re.search(r'(?:set\s+)?(?:labor\s+)?budget\s+(?:to\s+)?(?:£\s*)?(\d[\d,\.]+)', lower) or re.search(r'spend\s+(?:max\s+)?(?:on\s+labor\s+)?(?:to\s+)?(?:£\s*)?(\d[\d,\.]+)', lower)
    if budget_match:
        val_str = budget_match.group(1).replace(",", "")
        try:
            budget = float(val_str)
            state["weekly_budget"] = budget
            return f"💰 Weekly labor budget updated to **£{budget:,.2f}**. The mathematical solver guarantees payroll will stay within this envelope.", state, True
        except ValueError:
            pass

    # 3. GENERATE COMMAND
    if any(kw in lower for kw in ["generate", "make rota", "show rota", "run rota", "create rota", "build rota", "solve rota"]):
        mode = "powerhouse" if any(p in lower for p in ["power", "pay", "busy", "rush"]) else "balanced"
        is_pay = True if any(p in lower for p in ["pay", "month end", "power"]) else state.get("is_pay_week", False)
        state["mode"] = mode
        state["is_pay_week"] = is_pay
        return f"⚡ Calculating **{mode.title()} Rota** (Pay Week: {is_pay}) against all Global & Local boundaries...", state, True

    # 4. ADD NEW WORKER COMMAND
    if "add" in lower and any(w in lower for w in ["user", "worker", "staff", "member", "employee"]):
        name_match = re.search(r'(?:user|worker|staff|member|employee)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', raw, re.IGNORECASE)
        worker_name = name_match.group(1) if name_match else "New Worker"
        
        # Skills
        skills = []
        if any(kw in lower for kw in ["front", "foh", "counter", "till", "sell"]):
            skills.extend(["FOH", "Till", "Serve", "Sets"])
        if any(kw in lower for kw in ["kitchen", "cook", "grill", "fryer"]):
            skills.extend(["Grill", "Fryers", "Sets"])
        if "grill" in lower and "Grill" not in skills:
            skills.append("Grill")
        if "fryer" in lower and "Fryers" not in skills:
            skills.append("Fryers")
        if not skills:
            skills = ["FOH", "Sets", "Fryers"]

        hrs_match = re.search(r'(\d+)\s*(?:hours|hrs|h)', lower)
        max_h = float(hrs_match.group(1)) if hrs_match else 20.0

        rate_match = re.search(r'(\d+\.\d{2})', lower) or re.search(r'£\s*(\d+[\.\d]*)', lower)
        rate = float(rate_match.group(1)) if rate_match else 11.44

        avail_days = extract_days(lower)
        avail = ", ".join(avail_days) if avail_days else "Any"

        new_worker = {
            "id": worker_name.lower().replace(" ", "_"),
            "name": worker_name.title(),
            "role": "Team Member",
            "is_keyholder": False,
            "primary_dept": "Kitchen" if ("Grill" in skills or "Fryers" in skills) else "FOH",
            "skills": skills,
            "max_weekly_hours": max_h,
            "manager_weekly_cap": max_h,
            "hourly_rate": rate,
            "availability": avail,
            "notes": "Added via AI chat assistant."
        }
        state["staff_list"].append(new_worker)
        return f"👤 Added team member **{new_worker['name']}** ({', '.join(skills)}) | Max: {max_h}h | Rate: £{rate:.2f}/hr | Available: {avail}. Added to user directory!", state, True

    # 5. RESOLVE TARGET EMPLOYEE
    staff_match = resolve_staff(lower, staff_list)

    if staff_match:
        sid, sname = staff_match
        chosen_scope = scope or ("LOCAL" if any(w in lower for w in ["off", "holiday", "sick", "leave", "away"]) else "GLOBAL")
        target_rule_list = state["global_rules"] if chosen_scope == "GLOBAL" else state["local_rules"]
        badge = "🔒 Global Boundary (Permanent)" if chosen_scope == "GLOBAL" else "⚡ Local Boundary (This Week Only)"

        days = extract_days(lower)

        # A. WORKS ONLY ON SPECIFIC DAYS (e.g. "Taylor works only sundays", "Jordan only mon and tue")
        if "only" in lower and days and not any(w in lower for w in ["finish", "leave", "up to", "until", "start", "after", "before"]):
            new_rule = {
                "id": f"rule_{chosen_scope.lower()}_{sid}_only_days_{len(target_rule_list)+1}",
                "scope": chosen_scope,
                "target_type": "EMPLOYEE",
                "target_id": sid,
                "rule_type": "WORKS_ONLY_DAYS",
                "value": days,
                "description": f"{sname} works ONLY on {', '.join(days)}."
            }
            target_rule_list[:] = [r for r in target_rule_list if not (r.get("target_id") == sid and r.get("rule_type") in ["WORKS_ONLY_DAYS", "BLOCKED_DAYS"])]
            target_rule_list.append(new_rule)
            return f"{badge}: **{new_rule['description']}** has been saved and enforced.", state, True

        # B. DAY-SPECIFIC OR GENERAL TIMING RESTRICTION (e.g. "On Fridays Jordan works up to 6pm only", "Sam latest finish is 20:00")
        is_finish = any(w in lower for w in ["finish", "leave", "up to", "upto", "until", "past", "latest"])
        is_start = any(w in lower for w in ["start", "before", "after", "earliest"])
        
        if is_finish or is_start:
            time_str = extract_time_str(lower)
            if time_str:
                rule_type = "LATEST_FINISH" if is_finish else "EARLIEST_START"
                day_desc = f" on {', '.join(days)}" if days else ""
                new_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_time_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": rule_type,
                    "days": days or [],
                    "value": time_str,
                    "description": f"{sname} {('latest allowed finish is ' + time_str) if is_finish else ('earliest allowed start is ' + time_str)}{day_desc}."
                }
                target_rule_list.append(new_rule)
                return f"{badge}: **{new_rule['description']}** has been saved and enforced.", state, True

        # C. BLOCKED DAYS / NEVER WORKS ON DAYS (e.g. "Alex never works sundays and tuesdays")
        if any(w in lower for w in ["never work", "doesnt work", "doesn't work", "cannot work on", "not working on", "blocked on"]):
            if days:
                new_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_blocked_days_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "BLOCKED_DAYS",
                    "value": days,
                    "description": f"{sname} is BLOCKED from working on: {', '.join(days)}."
                }
                target_rule_list.append(new_rule)
                return f"{badge}: **{new_rule['description']}** has been saved and enforced.", state, True

        # D. LEAVE / HOLIDAY / OFF THIS WEEK (e.g. "Morgan is off this Thursday and Friday")
        if any(w in lower for w in ["off", "holiday", "leave", "sick", "unavailable", "away"]):
            if days:
                if sid not in state["leave"]:
                    state["leave"][sid] = []
                for d in days:
                    if d not in state["leave"][sid]:
                        state["leave"][sid].append(d)
                return f"🏖️ **{sname}** marked as OFF / on leave on: **{', '.join(days)}** for this upcoming week.", state, True
            elif "all week" in lower or "entire week" in lower:
                state["leave"][sid] = "All"
                return f"🏖️ **{sname}** marked as OFF for the entire week.", state, True

        # E. BLOCKED SHIFTS (e.g. "Alex never closes and doesn't work in mornings")
        blocked_shifts = []
        if any(w in lower for w in ["never close", "cannot close", "no close", "doesnt close", "doesn't close"]):
            blocked_shifts.append("Close")
        if any(w in lower for w in ["never morning", "cannot morning", "no morning", "doesnt work in morning", "doesn't work in morning", "no morn"]):
            blocked_shifts.append("Morning")
        if blocked_shifts:
            new_rule = {
                "id": f"rule_{chosen_scope.lower()}_{sid}_blocked_shifts_{len(target_rule_list)+1}",
                "scope": chosen_scope,
                "target_type": "EMPLOYEE",
                "target_id": sid,
                "rule_type": "BLOCKED_SHIFTS",
                "value": blocked_shifts,
                "description": f"{sname} never works {', '.join(blocked_shifts)} shifts."
            }
            target_rule_list.append(new_rule)
            return f"{badge}: **{new_rule['description']}** has been saved and enforced.", state, True

        # F. HOUR CAP / LIMIT (e.g. "Limit Jordan to 20 hours next week")
        hrs_match = re.search(r'(?:to|at|max|limit)\s*(\d+[\.\d]*)\s*(?:hours|hrs|h)?', lower)
        if any(w in lower for w in ["limit", "cap", "max hours", "maximum hours", "give"]):
            if hrs_match:
                hrs = float(hrs_match.group(1))
                state["cap_overrides"][sid] = hrs
                new_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_max_hours_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "MAX_HOURS",
                    "value": hrs,
                    "description": f"Cap {sname} to maximum {hrs} hours per week."
                }
                target_rule_list[:] = [r for r in target_rule_list if not (r.get("target_id") == sid and r.get("rule_type") == "MAX_HOURS")]
                target_rule_list.append(new_rule)
                return f"{badge}: Cap for **{sname}** set to **{hrs} hours**.", state, True

        # G. STATION LOCK (e.g. "Sam grill only", "Sam is grill master")
        if any(w in lower for w in ["grill master", "grill only", "only grill", "foh only", "only foh"]):
            station = "Grill" if "grill" in lower else "FOH"
            new_rule = {
                "id": f"rule_{chosen_scope.lower()}_{sid}_station_{len(target_rule_list)+1}",
                "scope": chosen_scope,
                "target_type": "EMPLOYEE",
                "target_id": sid,
                "rule_type": "STATION_LOCK",
                "value": station,
                "description": f"{sname} is dedicated exclusively to {station} station."
            }
            target_rule_list.append(new_rule)
            return f"{badge}: **{new_rule['description']}** has been saved and enforced.", state, True

    # 6. RESET COMMAND
    if any(w in lower for w in ["reset", "clear overrides", "start over"]):
        state["leave"] = {}
        state["cap_overrides"] = {}
        state["local_rules"] = []
        return "🔄 All local weekly overrides and leaves have been cleared for a fresh schedule.", state, True

    # FALLBACK HELPFUL GUIDANCE
    return (
        f"🤖 I received: *\"{raw}\"*\n\n"
        "Here are examples of commands you can type, or use the **User Dropdown** in the **Rules & Boundaries Manager** tab:\n"
        "• *'On Fridays, Jordan works up to 6pm only'*\n"
        "• *'On Wednesdays, Sam cannot work before 2pm'*\n"
        "• *'Global rule: Taylor works only on weekends'*\n"
        "• *'Alex never closes and doesn't work on Sundays'*\n"
        "• *'Morgan is off this Thursday and Friday'*\n"
        "• *'Limit Casey to 20 hours next week'*\n"
        "• *'Limit FOH to 3 people max'*\n"
        "• *'Set labor budget to £3,800'*"
    ), state, False
