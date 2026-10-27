import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dynamic_solver, rota_engine

rules = [
  {"id": "r1", "scope": "GLOBAL", "target_type": "STORE", "target_id": "ALL", "rule_type": "MANDATORY_DAYS_OFF", "value": 2, "description": "2 days off"},
  {"id": "r2", "scope": "GLOBAL", "target_type": "EMPLOYEE", "target_id": "sam_taylor", "rule_type": "LATEST_FINISH", "value": "20:00", "description": "Sam max 8pm"},
  {"id": "r3", "scope": "GLOBAL", "target_type": "EMPLOYEE", "target_id": "jordan_lee", "rule_type": "BLOCKED_SHIFTS", "value": ["Close"], "description": "Jordan no close"},
  {"id": "r4", "scope": "GLOBAL", "target_type": "EMPLOYEE", "target_id": "morgan_davis", "rule_type": "BLOCKED_DAYS", "value": ["Sun"], "description": "Morgan no Sun"}
]

res = dynamic_solver.solve_universal_rota(
    staff_list=rota_engine.DEFAULT_STAFF,
    store_hours=rota_engine.DEFAULT_GLOBAL_RULES['store_hours'],
    global_rules=rules,
    weekly_rules={},
    mode='balanced',
    weekly_budget=4000.0
)

print('Dynamic Solver Status:', res['status'])
print(f"Total Hours: {res['total_hours']}h | Variable Payroll: £{res['variable_payroll']:,.2f}")
for d in ['Mon', 'Tue', 'Fri']:
    print(f"\n=== {d} ===")
    for s in res['roster'][d]:
        print(f"  {s['time']:15s} | {s['assigned_to']:25s} | {s['desc']}")
