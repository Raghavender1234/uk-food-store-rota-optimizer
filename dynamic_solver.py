"""
Universal UK Food Store Rota Optimization Engine - Production CP-SAT Architecture
100% Dynamic - ZERO hardcoded names or rigid rules in code.
Every rule is stored as data (Global vs Local) and evaluated dynamically by the solver.
"""

from ortools.sat.python import cp_model
from typing import List, Dict, Any, Optional
import copy
import random

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ==============================================================================
# DYNAMIC SHIFT BUILDER
# ==============================================================================

def build_shifts_for_store(store_hours: Dict[str, Any], is_pay_week: bool = False, surge_rules: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Builds the operational shift slots from the store's configured opening hours.
    Supports dynamic local event surges (e.g. MK Stadium matches, concerts, peak rushes).
    """
    shifts = []
    
    for day in DAYS:
        day_cfg = store_hours.get(day, {"open": "09:00", "close": "22:45", "order_day": False})
        open_time = day_cfg.get("open", "09:00")
        close_time = day_cfg.get("close", "22:45")
        is_order_day = day_cfg.get("order_day", False)
        is_weekend_peak = day in ["Fri", "Sat"] or (is_pay_week and day == "Sun")

        close_hours = 7.0 if ("23:00" in close_time or "23:30" in close_time) else 6.25

        # 1. Opening Shift
        if is_order_day:
            # Monday delivery & ordering open (standard full shift runs to 16:00, but adapts dynamically if worker finishes earlier)
            order_finish = day_cfg.get("order_finish", "16:00")
            order_paid = 8.5 if order_finish == "16:00" else (8.0 if order_finish == "15:30" else (6.5 if order_finish == "14:00" else 8.0))
            shifts.append({
                "id": f"{day}_Order_Open",
                "day": day,
                "time": f"07:00 - {order_finish}",
                "start": "07:00",
                "finish": order_finish,
                "paid_hours": order_paid,
                "dept": "FOH",
                "req_skill": "FOH",
                "requires_keyholder": True,
                "flexible_finish": True,
                "allowed_roles": ["General Manager", "Assistant Manager", "Team Leader"],
                "desc": f"Food Delivery, Stock Ordering & Store Open"
            })
            # Other team members start at standard 09:00 AM opening, NOT 07:00 AM
            store_open_for_team = "09:00"
        else:
            shifts.append({
                "id": f"{day}_Morn_FOH",
                "day": day,
                "time": f"{open_time} - 16:00",
                "start": open_time,
                "finish": "16:00",
                "paid_hours": 6.5,
                "dept": "FOH",
                "req_skill": "FOH",
                "requires_keyholder": False,
                "desc": "Morning FOH Till & Counter"
            })
            store_open_for_team = open_time

        # Morning Kitchen Line (starts at standard 09:00 on Monday, not 07:00)
        shifts.append({
            "id": f"{day}_Morn_Kitch_Line",
            "day": day,
            "time": f"{store_open_for_team} - 16:00",
            "start": store_open_for_team,
            "finish": "16:00",
            "paid_hours": 6.5,
            "dept": "Kitchen",
            "req_skill": "Prep",
            "requires_keyholder": False,
            "desc": "Morning Kitchen Main Line"
        })

        # Morning Part-Time / Prep (starts at standard 09:00 on Monday, not 07:00)
        if day in ["Tue", "Wed", "Thu", "Fri"]:
            shifts.append({
                "id": f"{day}_Morn_PartTime",
                "day": day,
                "time": f"{store_open_for_team} - 14:00",
                "start": store_open_for_team,
                "finish": "14:00",
                "paid_hours": 5.0,
                "dept": "FOH",
                "req_skill": "FOH",
                "requires_keyholder": False,
                "desc": "FOH Morning Counter (Part-time)"
            })
        else:
            shifts.append({
                "id": f"{day}_Morn_Prep",
                "day": day,
                "time": f"{store_open_for_team} - 14:00",
                "start": store_open_for_team,
                "finish": "14:00",
                "paid_hours": 5.0,
                "dept": "Kitchen",
                "req_skill": "Prep",
                "requires_keyholder": False,
                "desc": "Kitchen Prep & Stock"
            })

        # 2. Mid Shifts (Peak Days)
        if is_weekend_peak:
            shifts.append({
                "id": f"{day}_Mid_Kitch",
                "day": day,
                "time": f"12:00 - {close_time}",
                "start": "12:00",
                "finish": close_time,
                "paid_hours": 10.5,
                "dept": "Kitchen",
                "req_skill": "Grill",
                "requires_keyholder": False,
                "desc": "Busy Mid-Day Kitchen Anchor till Close"
            })
        elif day in ["Wed", "Thu"] and not is_pay_week:
            shifts.append({
                "id": f"{day}_Trainer_Mid",
                "day": day,
                "time": "14:00 - 22:45",
                "start": "14:00",
                "finish": "22:45",
                "paid_hours": 8.25,
                "dept": "Kitchen",
                "req_skill": "Grill",
                "requires_keyholder": True,
                "desc": "Afternoon Line & Grill Master Close"
            })

        # 3. Evening Closes
        shifts.append({
            "id": f"{day}_Eve_FOH_Close",
            "day": day,
            "time": f"16:00 - {close_time}",
            "start": "16:00",
            "finish": close_time,
            "paid_hours": close_hours,
            "dept": "FOH",
            "req_skill": "FOH",
            "requires_keyholder": True,
            "desc": "FOH Closing Manager / Keyholder"
        })

        shifts.append({
            "id": f"{day}_Eve_Grill",
            "day": day,
            "time": f"16:00 - {close_time}",
            "start": "16:00",
            "finish": close_time,
            "paid_hours": close_hours,
            "dept": "Kitchen",
            "req_skill": "Grill",
            "requires_keyholder": False,
            "desc": "Kitchen Grill Master Close"
        })

        shifts.append({
            "id": f"{day}_Eve_Fryers",
            "day": day,
            "time": f"16:00 - {close_time}",
            "start": "16:00",
            "finish": close_time,
            "paid_hours": close_hours,
            "dept": "Kitchen",
            "req_skill": "Fryers",
            "requires_keyholder": False,
            "desc": "Kitchen Fryers & Assembly Close"
        })

        # 4. Dinner Rush Support
        if is_weekend_peak:
            shifts.append({
                "id": f"{day}_Eve_Sets_Rush",
                "day": day,
                "time": "17:00 - 22:30",
                "start": "17:00",
                "finish": "22:30",
                "paid_hours": 5.5,
                "dept": "Kitchen",
                "req_skill": "Sets",
                "requires_keyholder": False,
                "desc": "Kitchen Sets Peak Trade Support"
            })
            shifts.append({
                "id": f"{day}_Eve_Shakes_Expo",
                "day": day,
                "time": "17:00 - 22:30",
                "start": "17:00",
                "finish": "22:30",
                "paid_hours": 5.5,
                "dept": "FOH",
                "req_skill": "Shakes",
                "requires_keyholder": False,
                "desc": "FOH Shakes, Till & Expo Break Cover"
            })
        else:
            shifts.append({
                "id": f"{day}_Eve_PartTime_Support",
                "day": day,
                "time": "16:00 - 21:00",
                "start": "16:00",
                "finish": "21:00",
                "paid_hours": 5.0,
                "dept": "Flexible",
                "req_skill": "Sets",
                "requires_keyholder": False,
                "desc": "Evening Dinner Rush Support"
            })

        # 5. Local Event Demand Surge (e.g. MK Stadium Match, Concerts, Friday/Saturday Rush)
        if surge_rules:
            for rule in surge_rules:
                r_days = rule.get("days", [])
                if isinstance(r_days, str):
                    r_days = [r_days]
                r_days = [d.capitalize()[:3] for d in r_days]
                if day in r_days:
                    depts = rule.get("depts", ["FOH", "Kitchen"])
                    count = int(rule.get("extra_count", 1))
                    reason = rule.get("reason", "Event Demand Surge")
                    for i in range(count):
                        if "FOH" in depts:
                            shifts.append({
                                "id": f"{day}_Match_Surge_FOH_{i+1}",
                                "day": day,
                                "time": "17:00 - 22:30",
                                "start": "17:00",
                                "finish": "22:30",
                                "paid_hours": 5.5,
                                "dept": "FOH",
                                "req_skill": "FOH",
                                "requires_keyholder": False,
                                "desc": f"{reason} - Extra FOH Match Crowd Till & Expediter"
                            })
                        if "Kitchen" in depts:
                            shifts.append({
                                "id": f"{day}_Match_Surge_Kitch_{i+1}",
                                "day": day,
                                "time": "16:30 - 22:30",
                                "start": "16:30",
                                "finish": "22:30",
                                "paid_hours": 5.5,
                                "dept": "Kitchen",
                                "req_skill": "Fryers",
                                "requires_keyholder": False,
                                "desc": f"{reason} - Extra Kitchen Match Rush Line Support"
                            })

    return shifts

# ==============================================================================
# UNIVERSAL CONSTRAINT SOLVER
# Evaluates dynamic rules from state without hardcoding worker names
# ==============================================================================

def solve_universal_rota(
    staff_list: List[Dict[str, Any]],
    store_hours: Dict[str, Any],
    global_rules: List[Dict[str, Any]],
    weekly_rules: Dict[str, Any],
    mode: str = "balanced",
    is_pay_week: bool = False,
    weekly_budget: Optional[float] = 4000.0,
    seed: int = 42
) -> Dict[str, Any]:
    active_staff = copy.deepcopy(staff_list)
    
    # 1. Filter out inactive staff
    inactive_ids = set(weekly_rules.get("inactive_staff", []))
    active_staff = [s for s in active_staff if s["id"] not in inactive_ids]

    # 2. Add local weekly staff if any
    for new_s in weekly_rules.get("add_staff", []):
        if not any(s["id"] == new_s["id"] for s in active_staff):
            active_staff.append(new_s)

    # 3. Apply local cap overrides
    cap_overrides = weekly_rules.get("cap_overrides", {})
    for s in active_staff:
        if s["id"] in cap_overrides:
            s["manager_weekly_cap"] = cap_overrides[s["id"]]

    # 4. Extract event surge rules and build shifts
    all_rules_pre = list(global_rules) + list(weekly_rules.get("local_rules", []))
    surge_rules = [r for r in all_rules_pre if r.get("rule_type") in ["EVENT_SURGE", "MATCH_SURGE", "SURGE_STAFF"]]
    shifts = build_shifts_for_store(store_hours, is_pay_week=is_pay_week, surge_rules=surge_rules)

    model = cp_model.CpModel()
    
    # Decision variables: x[s, w] = 1 if worker w is assigned to shift s
    x = {}
    for s_idx in range(len(shifts)):
        for w_idx in range(len(active_staff)):
            x[s_idx, w_idx] = model.NewBoolVar(f"x_{s_idx}_{w_idx}")

    # Exactly 1 worker per shift slot
    for s_idx in range(len(shifts)):
        model.Add(sum(x[s_idx, w_idx] for w_idx in range(len(active_staff))) == 1)

    # Max 1 shift per day per worker
    day_work_vars = {}
    for day in DAYS:
        day_indices = [i for i, s in enumerate(shifts) if s["day"] == day]
        for w_idx in range(len(active_staff)):
            day_work_vars[day, w_idx] = model.NewBoolVar(f"works_{day}_{w_idx}")
            day_sum = sum(x[s_idx, w_idx] for s_idx in day_indices)
            model.Add(day_sum <= 1)
            model.Add(day_work_vars[day, w_idx] == day_sum)

    # Base Qualification & Availability Constraints
    for s_idx, s in enumerate(shifts):
        for w_idx, w in enumerate(active_staff):
            var = x[s_idx, w_idx]

            # Skill & Department matching
            req_skill = s.get("req_skill")
            dept = s.get("dept")
            if req_skill:
                w_skills = set(w.get("skills", []))
                w_dept = w.get("primary_dept", "Flexible")
                is_leadership = w.get("role") in ["General Manager", "Store Manager", "Assistant Manager", "Team Leader", "Store Trainer"]
                matches_skill = (req_skill in w_skills)
                matches_dept = (dept in w_skills or dept == w_dept or w_dept == "Flexible" or dept == "Flexible")
                if not (matches_skill or (matches_dept and is_leadership) or (matches_dept and req_skill in ["Sets", "Shakes", "Till", "Expo", "Serve", "Prep"])):
                    model.Add(var == 0)
                    continue

            # Keyholder matching
            if s.get("requires_keyholder", False) and not w.get("is_keyholder", False):
                model.Add(var == 0)
                continue

            # Specific role restrictions (e.g. Monday 07:00 AM stock delivery open is GM or AM only)
            allowed_roles = s.get("allowed_roles")
            if allowed_roles and w.get("role") not in allowed_roles:
                model.Add(var == 0)
                continue

            # Availability by Day
            if w.get("availability") != "Any":
                allowed_days = [d.strip() for d in w["availability"].split(",")]
                if s["day"] not in allowed_days:
                    model.Add(var == 0)
                    continue

    # -------------------------------------------------------------------------
    # DYNAMIC RULE COMPILER & EVALUATOR
    # Iterates over all rules configured in state (Global & Local)
    # -------------------------------------------------------------------------
    all_rules = list(global_rules)
    
    # Local holiday / leave rules
    leave_map = weekly_rules.get("leave", {})
    for staff_id, days_off in leave_map.items():
        all_rules.append({
            "scope": "LOCAL",
            "target_type": "EMPLOYEE",
            "target_id": staff_id,
            "rule_type": "LEAVE_DAYS",
            "value": days_off,
            "description": f"Leave: {staff_id} off on {days_off}"
        })

    # Pre-scan for manager specific assignments to exempt from general blocks
    must_work_map = set()   # (worker_id, day_lower)
    morn_exempt_map = set() # (worker_id, day_lower)
    peak_exempt_map = set() # (worker_id, day_lower)

    for rule in all_rules:
        r_type = rule.get("rule_type")
        tid = rule.get("target_id")
        r_days = rule.get("days") or rule.get("value")
        if isinstance(r_days, (int, float)):
            r_days = []
        elif isinstance(r_days, str):
            r_days = [r_days]
        if not r_days:
            r_days = DAYS
        day_tokens = [str(d).strip().lower()[:3] for d in r_days if str(d).strip()]

        if r_type in ["MUST_WORK_DAYS", "LOCKED_DAYS", "WORKS_ON_DAYS"]:
            for d in day_tokens:
                must_work_map.add((tid, d))
        elif r_type in ["REQUIRE_MORNING_HOURS", "MORNING_HOURS"]:
            for d in day_tokens:
                morn_exempt_map.add((tid, d))
                must_work_map.add((tid, d))
        elif r_type in ["REQUIRE_PEAK_HOURS", "PEAK_HOURS"]:
            for d in day_tokens:
                peak_exempt_map.add((tid, d))
                must_work_map.add((tid, d))

    for rule in all_rules:
        target_type = rule.get("target_type")
        target_id = rule.get("target_id")
        rule_type = rule.get("rule_type")
        val = rule.get("value")

        # RULE: MANDATORY MINIMUM DAYS OFF PER WEEK (e.g. 2 days off -> max 5 days worked)
        if rule_type == "MANDATORY_DAYS_OFF":
            min_days_off = int(val)
            max_days_work = 7 - min_days_off
            for w_idx in range(len(active_staff)):
                model.Add(sum(day_work_vars[day, w_idx] for day in DAYS) <= max_days_work)

        # RULE: LOCKED TO SPECIFIC SHIFTS / DAYS (e.g. Student weekend shifts)
        elif rule_type == "LOCKED_SHIFTS":
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    allowed_shift_ids = val if isinstance(val, list) else [val]
                    for s_idx, s in enumerate(shifts):
                        if s["id"] not in allowed_shift_ids:
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: MUST WORK ON SPECIFIC DAYS (e.g. Luke wants Stella on Monday, Barry on Friday)
        elif rule_type in ["MUST_WORK_DAYS", "LOCKED_DAYS", "WORKS_ON_DAYS"]:
            target_days = val if isinstance(val, list) else [val]
            target_days = [d.capitalize()[:3] for d in target_days]
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    for d in target_days:
                        if (d, w_idx) in day_work_vars:
                            model.Add(day_work_vars[d, w_idx] == 1)

        # RULE: REQUIRE PEAK HOURS / DINNER RUSH (e.g. Raghavender on Friday and Saturday in peak hours)
        elif rule_type in ["REQUIRE_PEAK_HOURS", "PEAK_HOURS"]:
            target_days = [d.capitalize()[:3] for d in (rule.get("days") or (val if isinstance(val, list) else [val] if val else DAYS))]
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    for d in target_days:
                        peak_shifts = [
                            s_idx for s_idx, s in enumerate(shifts)
                            if s["day"] == d and (
                                any(t in s.get("time", "") for t in ["16:00", "17:00", "22:45", "23:00", "23:30"])
                                or any(k in s.get("desc", "").lower() for k in ["close", "dinner", "rush", "grill", "fryers"])
                            )
                        ]
                        if peak_shifts:
                            model.Add(sum(x[s_idx, w_idx] for s_idx in peak_shifts) >= 1)

        # RULE: REQUIRE MORNING HOURS (e.g. Albert on Tuesday and Thursday morning)
        elif rule_type in ["REQUIRE_MORNING_HOURS", "MORNING_HOURS"]:
            target_days = [d.capitalize()[:3] for d in (rule.get("days") or (val if isinstance(val, list) else [val] if val else DAYS))]
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    for d in target_days:
                        morn_shifts = [
                            s_idx for s_idx, s in enumerate(shifts)
                            if s["day"] == d and (
                                any(t in s.get("start", "") for t in ["07:00", "09:00", "10:00", "11:00"])
                                or "morn" in s["id"].lower()
                                or "open" in s["id"].lower()
                            )
                        ]
                        if morn_shifts:
                            model.Add(sum(x[s_idx, w_idx] for s_idx in morn_shifts) >= 1)

        # RULE: LATEST FINISH TIME (can apply to all days or specific days)
        elif rule_type == "LATEST_FINISH":
            max_finish = str(val).strip()  # e.g. "20:00" or "18:00"
            applicable_days = [d.lower()[:3] for d in rule.get("days", [])] if rule.get("days") else []
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        if applicable_days and s["day"].lower()[:3] not in applicable_days:
                            continue
                        finish = s.get("finish", "22:45")
                        time_str = s.get("time", "")

                        # Flexible shifts adapt dynamically to worker's limit
                        if s.get("flexible_finish"):
                            if max_finish < "13:30":
                                model.Add(x[s_idx, w_idx] == 0)
                            continue

                        # If finish is past max_finish or it's a late closing shift
                        if finish > max_finish or ("20:00" in max_finish and any(late in time_str for late in ["21:00", "22:00", "22:30", "22:45", "23:00", "23:30", "Close"])):
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: EARLIEST START TIME (can apply to all days or specific days)
        elif rule_type == "EARLIEST_START":
            min_start = str(val).strip()  # e.g. "12:00" or "14:00"
            applicable_days = [d.lower()[:3] for d in rule.get("days", [])] if rule.get("days") else []
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        if applicable_days and s["day"].lower()[:3] not in applicable_days:
                            continue
                        start = s.get("start", "09:00")
                        if start < min_start:
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: DAY SPECIFIC TIMING RESTRICTION (e.g. On Friday, finishes by 18:00)
        elif rule_type == "DAY_TIMING_RESTRICTION":
            applicable_days = [d.lower()[:3] for d in rule.get("days", [])] if rule.get("days") else []
            max_finish = rule.get("latest_finish") or (val if "finish" in str(rule.get("description", "")).lower() else None)
            min_start = rule.get("earliest_start") or (val if "start" in str(rule.get("description", "")).lower() else None)

            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        if applicable_days and s["day"].lower()[:3] not in applicable_days:
                            continue
                        if max_finish and s.get("finish", "22:45") > str(max_finish):
                            if s.get("flexible_finish") and str(max_finish) >= "13:30":
                                pass
                            else:
                                model.Add(x[s_idx, w_idx] == 0)
                        if min_start and s.get("start", "09:00") < str(min_start):
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: BLOCKED SHIFT TYPES (e.g. No Close, No Morning)
        elif rule_type == "BLOCKED_SHIFTS":
            raw_blocked = val if isinstance(val, list) else [val]
            blocked_types = [str(b).lower().strip() for b in raw_blocked]
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        s_day = s["day"].lower()[:3]
                        time_str = s.get("time", "").lower()
                        desc = s.get("desc", "").lower()
                        is_morn = any(m in time_str for m in ["07:00", "09:00", "10:00", "11:00", "12:00"]) or "morn" in s["id"].lower() or "prep" in desc
                        is_close = any(late in time_str for late in ["22:45", "23:00", "23:30"]) or "close" in desc
                        
                        if "morning" in blocked_types and is_morn:
                            if (w["id"], s_day) not in morn_exempt_map:
                                model.Add(x[s_idx, w_idx] == 0)
                        if "close" in blocked_types and is_close:
                            if (w["id"], s_day) not in peak_exempt_map:
                                model.Add(x[s_idx, w_idx] == 0)

        # RULE: BLOCKED SPECIFIC DAYS (e.g. No Tue, No Sun, or blocked days)
        elif rule_type == "BLOCKED_DAYS":
            if isinstance(val, str):
                raw_list = [d.strip().lower()[:3] for d in val.replace(",", " ").split() if d.strip()]
            else:
                raw_list = [str(d).strip().lower()[:3] for d in val]
            
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        s_day = s["day"].lower()[:3]
                        if s_day in raw_list:
                            if (w["id"], s_day) not in must_work_map:
                                model.Add(x[s_idx, w_idx] == 0)

        # RULE: WORKS ONLY SPECIFIC DAYS (e.g. Works only on Sundays)
        elif rule_type in ["WORKS_ONLY_DAYS", "ALLOWED_DAYS"]:
            if isinstance(val, str):
                allowed_list = [d.strip().lower()[:3] for d in val.replace(",", " ").split() if d.strip()]
            else:
                allowed_list = [str(d).strip().lower()[:3] for d in val]

            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id or target_id == "ALL":
                    for s_idx, s in enumerate(shifts):
                        s_day = s["day"].lower()[:3]
                        if s_day not in allowed_list:
                            if (w["id"], s_day) not in must_work_map:
                                model.Add(x[s_idx, w_idx] == 0)

        # RULE: SPECIFIC STATION LOCK (e.g. Grill Only, FOH Only)
        elif rule_type in ["STATION_LOCK", "ONLY_STATION"]:
            target_station = str(val).strip().lower()
            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    for s_idx, s in enumerate(shifts):
                        desc = s.get("desc", "").lower()
                        dept = s.get("dept", "").lower()
                        req_skill = s.get("req_skill", "").lower()
                        if target_station not in desc and target_station not in dept and target_station not in req_skill:
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: WEEKLY HOUR LIMIT / CAP OVERRIDE (e.g. Limit worker to 20h)
        elif rule_type in ["MAX_HOURS", "HOUR_CAP"]:
            try:
                max_h = float(val)
                for w in active_staff:
                    if w["id"] == target_id or target_id == "ALL":
                        w["manager_weekly_cap"] = min(w.get("manager_weekly_cap", max_h), max_h)
            except Exception:
                pass

        # RULE: MINIMUM HOURS IF SCHEDULED
        elif rule_type == "MIN_HOURS":
            try:
                min_h = float(val)
                min_tenths = int(min_h * 10)
                for w_idx, w in enumerate(active_staff):
                    if w["id"] == target_id:
                        tot_tenths = sum(int(shifts[s_idx]["paid_hours"] * 10) * x[s_idx, w_idx] for s_idx in range(len(shifts)))
                        model.Add(tot_tenths >= min_tenths)
            except Exception:
                pass

        # RULE: LEAVE / HOLIDAY
        elif rule_type == "LEAVE_DAYS":
            if val == "All":
                raw_days = [d.lower()[:3] for d in DAYS]
            elif isinstance(val, str):
                raw_days = [d.strip().lower()[:3] for d in val.replace(",", " ").split() if d.strip()]
            else:
                raw_days = [str(d).strip().lower()[:3] for d in val]

            for w_idx, w in enumerate(active_staff):
                if w["id"] == target_id:
                    for s_idx, s in enumerate(shifts):
                        if s["day"].lower()[:3] in raw_days:
                            model.Add(x[s_idx, w_idx] == 0)

        # RULE: MAXIMUM CONCURRENT FOH / KITCHEN ON A SHIFT (e.g. Max 3 FOH at any time)
        elif rule_type == "MAX_CONCURRENT_HEADCOUNT":
            dept = rule.get("dept", "FOH")
            max_count = int(val)
            for day in DAYS:
                dinner_shifts = [i for i, s in enumerate(shifts) if s["day"] == day and s.get("dept") == dept and "16:00" in s["time"]]
                if dinner_shifts and len(dinner_shifts) > max_count:
                    model.Add(sum(x[s_idx, w_idx] for s_idx in dinner_shifts for w_idx in range(len(active_staff))) <= max_count)

    # -------------------------------------------------------------------------
    # WEEKLY HOUR CAPS (Contract & Discretionary)
    # -------------------------------------------------------------------------
    for w_idx, w in enumerate(active_staff):
        cap_tenths = int(w.get("manager_weekly_cap", 30.0) * 10)
        tot_tenths = sum(int(shifts[s_idx]["paid_hours"] * 10) * x[s_idx, w_idx] for s_idx in range(len(shifts)))
        model.Add(tot_tenths <= cap_tenths)

    # -------------------------------------------------------------------------
    # DYNAMIC LABOR BUDGET CONSTRAINT
    # Salaried workers = £0.00 variable cost. Hourly workers count against budget.
    # -------------------------------------------------------------------------
    if weekly_budget is not None and weekly_budget > 0:
        budget_pence = int(weekly_budget * 100)
        total_cost_pence = sum(
            int(shifts[s_idx]["paid_hours"] * (0.0 if active_staff[w_idx].get("is_salaried") else active_staff[w_idx].get("hourly_rate", 11.44)) * 100) * x[s_idx, w_idx]
            for s_idx in range(len(shifts))
            for w_idx in range(len(active_staff))
        )
        model.Add(total_cost_pence <= budget_pence)

    # -------------------------------------------------------------------------
    # OBJECTIVES & SOFT PREFERENCES
    # -------------------------------------------------------------------------
    rng = random.Random(seed)
    obj_terms = []

    for s_idx, s in enumerate(shifts):
        pref_list = s.get("preferred_staff", [])
        for w_idx, w in enumerate(active_staff):
            weight = 0
            if w["id"] in pref_list:
                weight += 120

            # General Manager / Store Manager: Salaried, maximize utilization up to contract hours to save variable payroll
            if w.get("is_salaried") or w.get("salaried") or w.get("role") in ["General Manager", "Store Manager"]:
                weight += 250

            # Peak Dinner Leadership (16:00 - Close)
            # Efficiently deploy Team Leads, Supervisors, and Store Trainers in evening peak
            is_evening_peak = any(t in s.get("time", "") for t in ["16:00", "17:00", "22:45", "23:00", "23:30"]) or "Close" in s.get("desc", "")
            if is_evening_peak:
                if w.get("role") in ["Team Leader", "Shift Supervisor", "Store Trainer"]:
                    weight += 220
                elif w.get("is_keyholder"):
                    weight += 100

            # Grill preference for designated trainers / grillers
            if "Grill" in s.get("desc", "") and "Grill" in w.get("skills", []):
                weight += 100
                if w.get("role") == "Store Trainer":
                    weight += 150

            # FOH preference for Assistant Manager
            if s.get("dept") == "FOH" and w.get("role") == "Assistant Manager":
                weight += 150

            # Trade mode variations
            if mode == "powerhouse" and s["day"] in ["Fri", "Sat", "Sun"]:
                if w.get("role") in ["General Manager", "Store Trainer", "Team Leader"] or w.get("is_keyholder"):
                    weight += 180

            if mode == "balanced":
                weight += rng.randint(-5, 5)

            obj_terms.append(weight * x[s_idx, w_idx])

    model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solver.parameters.random_seed = seed
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        roster_by_day = {d: [] for d in DAYS}
        individual_hours = {w["name"]: 0.0 for w in active_staff}
        individual_cost = {w["name"]: 0.0 for w in active_staff}
        days_worked_count = {w["name"]: 0 for w in active_staff}
        days_off_list = {w["name"]: [] for w in active_staff}

        for day in DAYS:
            for w_idx, w in enumerate(active_staff):
                if solver.Value(day_work_vars[day, w_idx]) == 1:
                    days_worked_count[w["name"]] += 1
                else:
                    days_off_list[w["name"]].append(day)

        for s_idx, s in enumerate(shifts):
            for w_idx, w in enumerate(active_staff):
                if solver.Value(x[s_idx, w_idx]) == 1:
                    shift_finish = s["finish"]
                    shift_time = s["time"]
                    shift_paid = s["paid_hours"]

                    # If shift has flexible finish (e.g. Mon delivery open), dynamically adjust to worker's limit
                    if s.get("flexible_finish"):
                        day_rules = [r for r in all_rules if (r.get("target_id") in [w["id"], "ALL"]) and r.get("rule_type") in ["LATEST_FINISH", "DAY_TIMING_RESTRICTION"]]
                        worker_max_finish = None
                        for r in day_rules:
                            r_days = [d.lower()[:3] for d in r.get("days", [])] if r.get("days") else []
                            if not r_days or s["day"].lower()[:3] in r_days:
                                f_val = r.get("latest_finish") or r.get("value")
                                if f_val:
                                    worker_max_finish = str(f_val).strip()
                                    break
                        if worker_max_finish and worker_max_finish <= s["finish"]:
                            shift_finish = worker_max_finish
                            shift_time = f"{s['start']} - {shift_finish}"
                            start_h = float(s["start"].split(":")[0]) + float(s["start"].split(":")[1])/60.0
                            fin_h = float(shift_finish.split(":")[0]) + float(shift_finish.split(":")[1])/60.0
                            raw_dur = fin_h - start_h
                            break_dur = 0.5 if raw_dur >= 6.0 else 0.0
                            shift_paid = round(raw_dur - break_dur, 2)

                    rate = 0.0 if w.get("is_salaried") else w.get("hourly_rate", 11.44)
                    cost = round(shift_paid * rate, 2)
                    roster_by_day[s["day"]].append({
                        "shift_id": s["id"],
                        "time": shift_time,
                        "desc": f"{s['desc']} ({shift_time})",
                        "assigned_to": w["name"],
                        "role": w["role"],
                        "pay_tier": w.get("pay_tier", "Hourly"),
                        "is_salaried": w.get("is_salaried", False),
                        "paid_hours": shift_paid,
                        "hourly_rate": rate,
                        "cost": cost
                    })
                    individual_hours[w["name"]] += shift_paid
                    individual_cost[w["name"]] += cost

        total_hours = round(sum(individual_hours.values()), 2)
        variable_payroll = round(sum(individual_cost.values()), 2)

        return {
            "status": "SUCCESS",
            "mode": mode,
            "is_pay_week": is_pay_week,
            "roster": roster_by_day,
            "total_hours": total_hours,
            "variable_payroll": variable_payroll,
            "weekly_budget": weekly_budget,
            "budget_remaining": round(weekly_budget - variable_payroll, 2) if weekly_budget else None,
            "staff_hours": {k: round(v, 2) for k, v in individual_hours.items() if v > 0},
            "staff_costs": {k: round(v, 2) for k, v in individual_cost.items() if v > 0},
            "days_worked": days_worked_count,
            "days_off": days_off_list
        }
    else:
        return {
            "status": "INFEASIBLE",
            "message": "Could not satisfy all Global and Local boundaries with current settings."
        }
