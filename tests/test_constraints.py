import sys
sys.path.append(r'C:\Users\brred\.gemini\antigravity\scratch\milton_keynes_rota')
import rota_engine
from ortools.sat.python import cp_model

shifts = rota_engine.build_shifts_for_week(is_pay_week=False)
STAFF = rota_engine.STAFF

def test_model(include_caps=True, include_skills=True, include_max_one_per_day=True):
    model = cp_model.CpModel()
    x = {}
    for s_idx, s in enumerate(shifts):
        for w_idx, w in enumerate(STAFF):
            x[s_idx, w_idx] = model.NewBoolVar(f"x_{s_idx}_{w_idx}")

    # Constraint 1: One worker per shift
    for s_idx in range(len(shifts)):
        model.Add(sum(x[s_idx, w_idx] for w_idx in range(len(STAFF))) == 1)

    # Constraint 2: Eligibility & skills
    if include_skills:
        for s_idx, s in enumerate(shifts):
            for w_idx, w in enumerate(STAFF):
                var = x[s_idx, w_idx]
                if "locked_to" in s and w["id"] != s["locked_to"]:
                    model.Add(var == 0)
                    continue
                if "locked_shifts" in w and s["id"] not in w["locked_shifts"]:
                    model.Add(var == 0)
                    continue
                req_skill = s.get("req_skill")
                if req_skill and req_skill not in w["skills"]:
                    model.Add(var == 0)
                    continue
                if s.get("requires_keyholder", False) and not w["is_keyholder"]:
                    model.Add(var == 0)
                    continue
                if w["availability"] != "Any":
                    allowed_days = [d.strip() for d in w["availability"].split(",")]
                    if s["day"] not in allowed_days:
                        model.Add(var == 0)
                        continue
                if w.get("shift_restriction") == "Morning_Only":
                    if "Morn" not in s["id"] and "09:00" not in s["time"] and "07:00" not in s["time"]:
                        model.Add(var == 0)
                        continue

    # Constraint 3: Max one shift per day
    if include_max_one_per_day:
        for day in rota_engine.DAYS:
            day_shift_indices = [i for i, s in enumerate(shifts) if s["day"] == day]
            for w_idx in range(len(STAFF)):
                model.Add(sum(x[s_idx, w_idx] for s_idx in day_shift_indices) <= 1)

    # Constraint 4: Weekly caps
    if include_caps:
        for w_idx, w in enumerate(STAFF):
            cap = int(w["manager_weekly_cap"] * 10)
            tot = sum(int(shifts[s_idx]["paid_hours"] * 10) * x[s_idx, w_idx] for s_idx in range(len(shifts)))
            model.Add(tot <= cap)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

print("Base test (All constraints):", test_model(True, True, True))
print("Without caps:", test_model(False, True, True))
print("Without max_one_per_day:", test_model(True, True, False))
print("Without skills:", test_model(True, False, True))
