import sys
sys.path.append(r'C:\Users\brred\.gemini\antigravity\scratch\milton_keynes_rota')
import rota_engine

res = rota_engine.solve_rota(mode='balanced', is_pay_week=False)
print('Status:', res['status'])
if res['status'] == 'SUCCESS':
    print(f"Total Hours: {res['total_hours']}h | Variable Payroll: £{res['variable_payroll']:,.2f}")
    print("\n2 DAYS OFF GUARANTEE CHECK (EVERY WORKER HAS >= 2 DAYS OFF):")
    for name, off_days in res['days_off'].items():
        worked = res['days_worked'][name]
        print(f"  • {name:25s}: Worked {worked} days | OFF: {', '.join(off_days)} (Total off: {len(off_days)} days)")
