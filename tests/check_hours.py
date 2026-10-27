import sys
sys.path.append(r'C:\Users\brred\.gemini\antigravity\scratch\milton_keynes_rota')
import rota_engine
from ortools.sat.python import cp_model

shifts = rota_engine.build_shifts_for_week(is_pay_week=False)
STAFF = rota_engine.STAFF

model = cp_model.CpModel()
x = {}
for s_idx, s in enumerate(shifts):
    for w_idx, w in enumerate(STAFF):
        x[s_idx, w_idx] = model.NewBoolVar(f"x_{s_idx}_{w_idx}")

for s_idx in range(len(shifts)):
    model.Add(sum(x[s_idx, w_idx] for w_idx in range(len(STAFF))) == 1)

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

for day in rota_engine.DAYS:
    day_shift_indices = [i for i, s in enumerate(shifts) if s["day"] == day]
    for w_idx in range(len(STAFF)):
        model.Add(sum(x[s_idx, w_idx] for s_idx in day_shift_indices) <= 1)

# Solve without caps first to see what hours each person gets
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Hours needed per staff without caps:")
    for w_idx, w in enumerate(STAFF):
        hours = sum(shifts[s_idx]["paid_hours"] * solver.Value(x[s_idx, w_idx]) for s_idx in range(len(shifts)))
        print(f"  {w['name']:25s}: {hours:5.1f}h  (Current Cap: {w['manager_weekly_cap']}h)")
