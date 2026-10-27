import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dynamic_solver
import rota_engine

def print_week_roster(title, res):
    print("=" * 85)
    print(f" {title.upper()} (Total Paid Hours: {res.get('total_hours', 0)}h)")
    print("=" * 85)
    
    if res.get("status") != "SUCCESS":
        print(f"Status: {res.get('status')} - {res.get('message')}")
        return

    for day in dynamic_solver.DAYS:
        shifts = res["roster"][day]
        day_hours = sum(s["paid_hours"] for s in shifts)
        print(f"\n--- {day.upper()} ({len(shifts)} staff on duty | {day_hours:.1f}h) ---")
        for s in shifts:
            print(f"  {s['time']:15s} | {s['assigned_to']:25s} ({s['role']:15s}) -> {s['desc']}")

    print("\nSTAFF HOURS BREAKDOWN THIS WEEK:")
    for name, hrs in sorted(res["staff_hours"].items(), key=lambda x: -x[1]):
        print(f"  • {name:25s}: {hrs:5.1f}h")

# 1. RUN STANDARD WEEK (BALANCED)
res_std = dynamic_solver.solve_universal_rota(
    staff_list=rota_engine.DEFAULT_STAFF,
    store_hours=rota_engine.DEFAULT_GLOBAL_RULES["store_hours"],
    global_rules=[],
    weekly_rules={},
    mode="balanced"
)
print_week_roster("Scenario 1: Standard Week (Balanced & Fair)", res_std)

# 2. RUN WEEK 2 WITH USER MODIFICATIONS (HOLIDAYS, CAPS, NEW USER)
print("\n" + "#" * 85)
print(" SCENARIO 2: USER MODIFIES DETAILS FOR NEXT WEEK")
print(" Modifications Applied:")
print("   • Morgan Davis: ON LEAVE Friday & Saturday (Holiday)")
print("   • Jamie Wilson: ON LEAVE Wednesday")
print("   • Riley Johnson: Hours personally capped to 25.0h (Manager discretion)")
print("   • New Hire Added: 'Jordan Casey' (Certified on Grill, Fryers, Sets, FOH; Cap 20h)")
print("#" * 85)

weekly_modifications = {
    "leave": {
        "morgan_davis": ["Fri", "Sat"],
        "jamie_wilson": ["Wed"]
    },
    "cap_overrides": {
        "riley_johnson": 25.0
    },
    "add_staff": [
        {
            "id": "jordan_casey",
            "name": "Jordan Casey (New Hire)",
            "role": "Crew Member",
            "is_keyholder": False,
            "primary_dept": "Kitchen",
            "skills": ["Grill", "Fryers", "Sets", "FOH"],
            "max_weekly_hours": 25.0,
            "manager_weekly_cap": 20.0,
            "availability": "Any",
            "notes": "New versatile all-rounder hire."
        }
    ]
}

res_custom = dynamic_solver.solve_universal_rota(
    staff_list=rota_engine.DEFAULT_STAFF,
    store_hours=rota_engine.DEFAULT_GLOBAL_RULES["store_hours"],
    global_rules=[],
    weekly_rules=weekly_modifications,
    mode="balanced"
)
print_week_roster("Scenario 2: Next Week Custom Schedule", res_custom)
