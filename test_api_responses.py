"""
Test API responses to diagnose frontend issues
"""
from scripts.employee_tracker import EmployeeTracker
from config.target_companies import TARGET_COMPANIES
import json

print("\n" + "="*60)
print("API RESPONSE SIMULATION TEST")
print("="*60)

tracker = EmployeeTracker()

# Test 1: Get companies (simulating /companies endpoint)
print("\n1. TESTING /companies ENDPOINT LOGIC...")
db_companies = tracker.db.get_all_companies()
print(f"   get_all_companies() returned: {len(db_companies)} companies")
for comp in db_companies:
    print(f"   - {comp}")

employee_counts = tracker.db.get_company_employee_counts()
print(f"\n   get_company_employee_counts() returned: {len(employee_counts)} companies")
for comp, count in employee_counts.items():
    print(f"   - {comp}: {count} employees")

default_counts = tracker.db.get_all_company_defaults()
print(f"\n   get_all_company_defaults() returned: {len(default_counts)} companies")
for comp, default in default_counts.items():
    print(f"   - {comp}: default={default}")

# Simulate the /companies endpoint logic
target_companies_lower = [c.lower() for c in TARGET_COMPANIES]
custom_companies = []

for company_info in db_companies:
    company_name = company_info.get('company', '')
    if company_name.lower() not in target_companies_lower:
        custom_companies.append(company_name)

all_companies = TARGET_COMPANIES + custom_companies

print(f"\n   Final company list for UI:")
print(f"   - Predefined companies: {len(TARGET_COMPANIES)}")
print(f"   - Custom companies: {len(custom_companies)}")
print(f"   - Total companies: {len(all_companies)}")
print(f"\n   Companies: {all_companies}")

# Test 2: Get employees (simulating /track/employees endpoint)
print("\n2. TESTING /track/employees ENDPOINT LOGIC...")
employees = tracker.db.get_all_employees()
active_employees = [e for e in employees if e['status'] != 'deleted']

print(f"   Total employees: {len(employees)}")
print(f"   Active employees: {len(active_employees)}")
print(f"   Deleted employees: {len(employees) - len(active_employees)}")

if active_employees:
    print("\n   Sample active employees:")
    for emp in active_employees[:5]:
        print(f"   - {emp['name']} at {emp['company']} ({emp['status']})")

# Test 3: Check tracking status
print("\n3. TESTING /track/status ENDPOINT LOGIC...")
status = tracker.get_tracking_status()
print(f"   Status: {json.dumps(status, indent=2)}")

print("\n" + "="*60)
print("END OF API SIMULATION TEST")
print("="*60)
