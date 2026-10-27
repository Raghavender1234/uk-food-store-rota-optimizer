import sys
sys.path.append(r'C:\Users\brred\.gemini\antigravity\scratch\milton_keynes_rota')
import rota_engine

opt = rota_engine.solve_rota(mode='powerhouse', is_pay_week=True)
for day in ['Mon', 'Tue', 'Sat', 'Sun']:
    print(f"\n=== {day} ===")
    for s in opt['roster'][day]:
        print(f"  {s['time']:15s} | {s['assigned_to']:25s} | {s['desc']}")
