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

    # 0. Check verb-targeted staff first: e.g. "Luke wants Barry on Friday" -> targets Barry!
    action_match = re.search(r'\b(?:wants|want|make|keep|put|assign|schedule)\s+([a-z]+)', lower)
    if action_match:
        target_token = action_match.group(1).strip()
        for s in staff_list:
            full = s.get("name", "").lower()
            first = full.split()[0] if full else ""
            if target_token == first or target_token == s.get("id"):
                return s["id"], s.get("name")

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

def parse_time_token(raw_t: str, is_end: bool = False) -> Optional[str]:
    """Converts natural time tokens like '2 pm', '14:00', '7', 'close' into 24h format HH:MM."""
    raw_t = raw_t.strip().lower()
    if 'close' in raw_t:
        return '23:30'
    t_m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', raw_t)
    if not t_m:
        return None
    h = int(t_m.group(1))
    m = int(t_m.group(2)) if t_m.group(2) else 0
    ampm = t_m.group(3)
    if ampm == 'pm' and h < 12:
        h += 12
    elif ampm == 'am' and h == 12:
        h = 0
    elif not ampm:
        if h <= 6 or (is_end and h < 12 and h <= 6):
            h += 12
        elif is_end and h < 8:
            h += 12
    return f"{h:02d}:{m:02d}"

def extract_schedule_details(text: str) -> Tuple[Optional[str], Optional[str], bool, bool, bool]:
    """
    Extracts (start_time, finish_time, is_peak, is_morning, is_close) from natural text.
    """
    lower = text.lower()
    is_peak = any(w in lower for w in ['peak', 'rush', 'dinner', 'busy'])
    is_morn = any(w in lower for w in ['morning', 'open', 'opening', 'early'])
    is_close = any(w in lower for w in ['close', 'closing', 'night'])
    
    start_t, finish_t = None, None
    
    # 1. Range check like '5 to 9', '7 to 2', '7am to 2pm', '12 to 6', '4pm to close'
    range_match = re.search(r'(?:from\s*)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-|till|until)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|close)', lower)
    if range_match:
        start_t = parse_time_token(range_match.group(1), is_end=False)
        finish_t = parse_time_token(range_match.group(2), is_end=True)
    else:
        # Finish only (e.g. 'till 2 pm', 'until 4pm', 'by 2pm', 'up to 2pm', 'latest 6pm', 'finish by 2pm')
        fin_match = re.search(r'(?:till|until|by|up to|upto|latest|finish|ends? at|leave)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', lower)
        if fin_match:
            finish_t = parse_time_token(fin_match.group(1), is_end=True)
        # Start only (e.g. 'from 11am', 'starts at 10am', 'after 12pm', 'earliest 9am')
        start_match = re.search(r'(?:from|after|starts? at|starting at|earliest)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', lower)
        if start_match:
            start_t = parse_time_token(start_match.group(1), is_end=False)
            
    return start_t, finish_t, is_peak, is_morn, is_close

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

    # 1.5 EVENT DEMAND SURGE / MK STADIUM MATCH / EXTRA HEADCOUNT
    is_surge = any(kw in lower for kw in [
        "match", "stadium", "mk stadium", "game", "concert", "event",
        "more people", "extra people", "more staff", "extra staff",
        "boost staff", "surge", "busy night", "heavy trade", "crowd",
        "add one more", "add 1 more", "add two more", "add 2 more",
        "one more in", "extra in", "more in kitchen", "more in foh",
        "add extra", "put one more", "need one more", "need extra",
        "extra person", "more person", "extra worker", "one more person"
    ]) or (any(w in lower for w in ["add", "put", "need", "want"]) and any(w in lower for w in ["more", "extra"]) and any(w in lower for w in ["kitchen", "foh", "staff", "person", "rush", "peak"]))
    if is_surge:
        # Extract days
        surge_days = []
        for day_code, pat in DAY_PATTERNS.items():
            if re.search(pat, lower):
                surge_days.append(day_code)
        if not surge_days:
            if "weekend" in lower:
                surge_days = ["Fri", "Sat", "Sun"]
            elif "friday" in lower or "fri" in lower:
                surge_days = ["Fri"]
            elif "saturday" in lower or "sat" in lower:
                surge_days = ["Sat"]
            else:
                surge_days = ["Fri", "Sat"]

        # Extract departments
        surge_depts = []
        if any(w in lower for w in ["foh", "front", "counter", "till"]):
            surge_depts.append("FOH")
        if any(w in lower for w in ["kitchen", "kitch", "back", "line", "grill"]):
            surge_depts.append("Kitchen")
        if not surge_depts:
            surge_depts = ["FOH", "Kitchen"]

        # Extract extra count per dept (supports "one", "two", "three", "1", "2", etc.)
        num_words = {"one": 1, "two": 2, "three": 3, "four": 4, "a": 1, "an": 1}
        cnt_match = re.search(r'\b(\d+|one|two|three|four)\s*(?:more|extra)?\s*(?:in|person|people|staff|worker)?', lower)
        if cnt_match:
            raw_cnt = cnt_match.group(1).lower()
            extra_count = num_words.get(raw_cnt, int(raw_cnt) if raw_cnt.isdigit() else 1)
        else:
            extra_count = 1

        if any(w in lower for w in ["stadium", "match", "game"]):
            reason = "MK Stadium Match Surge"
        elif any(w in lower for w in ["peak", "rush", "dinner"]):
            reason = "Peak Rush Trade Surge"
        else:
            reason = "Extra Staff Demand Surge"

        chosen_scope = scope or "LOCAL"
        target_list = state["global_rules"] if chosen_scope == "GLOBAL" else state["local_rules"]

        # Remove previous matching surge rule to prevent duplicate accumulation
        target_list[:] = [r for r in target_list if not (r.get("rule_type") == "EVENT_SURGE" and any(d in r.get("days", []) for d in surge_days))]

        new_rule = {
            "id": f"rule_{chosen_scope.lower()}_event_surge_{len(target_list)+1}",
            "scope": chosen_scope,
            "target_type": "STORE",
            "target_id": "STORE",
            "rule_type": "EVENT_SURGE",
            "days": surge_days,
            "depts": surge_depts,
            "extra_count": extra_count,
            "reason": reason,
            "description": f"{reason} on {', '.join(surge_days)}: Injects extra {extra_count} peak shift(s) for {', '.join(surge_depts)}."
        }
        target_list.append(new_rule)
        badge = "🔒 Global Boundary" if chosen_scope == "GLOBAL" else "⚡ Local Boundary (This Week Only)"
        days_str = ", ".join(surge_days)
        depts_str = " & ".join(surge_depts)
        return (
            f"{badge}: **{reason}** activated for **{days_str}**!\n"
            f"• Injected extra peak-trade shifts for **{depts_str}** (16:30–22:30).\n"
            f"• Added **{extra_count} extra staff member(s)** to power through the rush while strictly maintaining UK break regulations and budget limits.",
            state,
            True
        )

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
        chosen_scope = scope or ("LOCAL" if any(w in lower for w in ["off", "holiday", "sick", "leave", "away", "this week"]) else "GLOBAL")
        target_rule_list = state["global_rules"] if chosen_scope == "GLOBAL" else state["local_rules"]
        badge = "🔒 Global Boundary (Permanent)" if chosen_scope == "GLOBAL" else "⚡ Local Boundary (This Week Only)"

        days = extract_days(lower)
        start_t, finish_t, is_peak, is_morn, is_close = extract_schedule_details(lower)

        # A. LEAVE / HOLIDAY / OFF THIS WEEK (e.g. "Barry is off this Thursday and Friday")
        if any(w in lower for w in ["off", "holiday", "leave", "sick", "unavailable", "away"]) and not any(w in lower for w in ["work on", "works on", "keep"]):
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

        # B. BLOCKED DAYS / NEVER WORKS ON DAYS (e.g. "Albert never works sundays and tuesdays")
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

        # C. BLOCKED SHIFTS (e.g. "Albert never closes and doesn't work in mornings")
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

        # D. WORKS ONLY ON SPECIFIC DAYS (e.g. "Taylor works only sundays", "Jordan only mon and tue")
        if "only" in lower and days and not (start_t or finish_t or is_peak or is_morn or is_close):
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

        # E. MANAGER SPECIFIC DAY SCHEDULER (Mandatory work day + peak hours / morning / specific time window)
        # e.g. "Stella works on Monday but till 2 pm"
        # e.g. "Make Raghavender work on Friday and Saturday mandatory in peak hours"
        # e.g. "Keep Albert on Tuesday and Thursday morning"
        # e.g. "Keep Albert on Friday from 12 to 6"
        # e.g. "Luke wants Barry on Friday 4pm to close"
        # e.g. "Assign Stella on Monday 7 to 2"
        is_sched_intent = any(w in lower for w in ["work on", "works on", "work", "works", "wants", "keep", "make", "assign", "strictly", "mandatory", "schedule", "put", "on monday", "on tuesday", "on wednesday", "on thursday", "on friday", "on saturday", "on sunday"])
        has_time_or_period = (start_t is not None) or (finish_t is not None) or is_peak or is_morn or is_close

        if days and (has_time_or_period or is_sched_intent):
            added_descs = []

            # Clean conflicting blocked days / shifts across both global and local rules
            for r_list in [state.get("global_rules", []), state.get("local_rules", [])]:
                for r in r_list:
                    if r.get("target_id") == sid:
                        if r.get("rule_type") == "BLOCKED_DAYS":
                            val = r.get("value", [])
                            if isinstance(val, list):
                                r["value"] = [d for d in val if d not in days]
                            elif isinstance(val, str) and val in days:
                                r["value"] = []
                        elif r.get("rule_type") == "BLOCKED_SHIFTS":
                            if is_morn and "Morning" in (r.get("value") or []):
                                r["value"] = [v for v in r.get("value") if v != "Morning"]
                            if (is_peak or is_close) and "Close" in (r.get("value") or []):
                                r["value"] = [v for v in r.get("value") if v != "Close"]
                r_list[:] = [r for r in r_list if r.get("value") != []]

            # 1. Mandatory Work Day Guarantee
            target_rule_list[:] = [r for r in target_rule_list if not (r.get("target_id") == sid and r.get("rule_type") == "MUST_WORK_DAYS")]
            must_work_rule = {
                "id": f"rule_{chosen_scope.lower()}_{sid}_must_work_{len(target_rule_list)+1}",
                "scope": chosen_scope,
                "target_type": "EMPLOYEE",
                "target_id": sid,
                "rule_type": "MUST_WORK_DAYS",
                "value": days,
                "description": f"{sname} MUST work on: {', '.join(days)}."
            }
            target_rule_list.append(must_work_rule)
            added_descs.append(f"scheduled to work on **{', '.join(days)}**")

            # 2. Peak Hours / Dinner Rush
            if is_peak or is_close:
                peak_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_peak_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "REQUIRE_PEAK_HOURS",
                    "days": days,
                    "description": f"{sname} assigned to PEAK RUSH / DINNER shifts on {', '.join(days)}."
                }
                target_rule_list.append(peak_rule)
                added_descs.append("during **PEAK RUSH hours (17:00–21:00/Close)**")

            # 3. Morning Shift
            if is_morn:
                morn_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_morn_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "REQUIRE_MORNING_HOURS",
                    "days": days,
                    "description": f"{sname} assigned to MORNING shifts on {', '.join(days)}."
                }
                target_rule_list.append(morn_rule)
                added_descs.append("on **MORNING shifts**")

            # 4. Start Time Restriction
            if start_t:
                start_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_start_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "EARLIEST_START",
                    "days": days,
                    "value": start_t,
                    "description": f"{sname} earliest start is {start_t} on {', '.join(days)}."
                }
                target_rule_list.append(start_rule)
                added_descs.append(f"starting from **{start_t}**")

            # 5. Finish Time Restriction (removes any previous conflicting finish rule for this person on these days)
            if finish_t:
                target_rule_list[:] = [r for r in target_rule_list if not (r.get("target_id") == sid and r.get("rule_type") in ["LATEST_FINISH", "DAY_TIMING_RESTRICTION"] and any(d in r.get("days", []) for d in days))]
                finish_rule = {
                    "id": f"rule_{chosen_scope.lower()}_{sid}_finish_{len(target_rule_list)+1}",
                    "scope": chosen_scope,
                    "target_type": "EMPLOYEE",
                    "target_id": sid,
                    "rule_type": "LATEST_FINISH",
                    "days": days,
                    "value": finish_t,
                    "description": f"{sname} latest finish is {finish_t} on {', '.join(days)}."
                }
                target_rule_list.append(finish_rule)
                added_descs.append(f"with finish by **{finish_t}**")

            summary_text = " ".join(added_descs)
            return f"{badge}: **{sname}** is {summary_text}.", state, True
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
