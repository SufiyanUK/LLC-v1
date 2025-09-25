"""
Tiered Monitoring System
Implements smart polling with VIP, Watch, and General tiers
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dotenv import load_dotenv

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

from src.data_collection.pdl_client import get_pdl_client
from src.monitoring.stealth_detector import StealthFounderDetector
from src.monitoring.employment_monitor import EmploymentMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TieredMonitoringSystem:
    """
    Manages tiered monitoring of employees with smart polling
    """
    
    def __init__(self, daily_budget: float = 5.0):
        """
        Initialize with daily budget constraint
        
        Args:
            daily_budget: Maximum daily spend in dollars
        """
        self.daily_budget = daily_budget
        self.cost_per_check = 0.01
        self.daily_checks_limit = int(daily_budget / self.cost_per_check)
        
        # Initialize components
        self.pdl_client = get_pdl_client()
        self.stealth_detector = StealthFounderDetector()
        self.employment_monitor = EmploymentMonitor()
        
        # Check allocations (can be adjusted)
        self.check_allocation = {
            'vip': 100,      # Check 100 VIP people daily
            'watch': 143,    # Check 1/7 of watch list daily (1000/7)
            'general': 333   # Check 1/30 of general list daily (10000/30)
        }
        
        logger.info(f"Initialized with daily budget: ${daily_budget}")
        logger.info(f"Daily check limit: {self.daily_checks_limit} employees")
    
    def fetch_employee_data(self, pdl_id: str) -> Optional[Dict]:
        """Fetch latest employee data from PDL"""
        try:
            params = {
                'params': {
                    'id': pdl_id
                }
            }
            response = self.pdl_client.person.retrieve(**params).json()
            
            if response.get('status') == 200:
                return response.get('data')
            else:
                logger.error(f"Failed to fetch {pdl_id}: {response}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {pdl_id}: {e}")
            return None
    
    def initial_bulk_analysis(self, company_names: List[str] = None, limit: int = 10000):
        """
        Perform initial bulk analysis of employees to categorize into tiers
        This is a one-time operation to set up the monitoring system
        """
        if not company_names:
            company_names = ['google', 'meta', 'facebook', 'apple', 'microsoft', 'openai', 'anthropic']
        
        logger.info(f"Starting initial bulk analysis for companies: {company_names}")
        
        all_employees = []
        for company in company_names:
            logger.info(f"Fetching employees from {company}...")
            
            # Build query for recent departures
            query = f'''
                past_company:"{company}" AND 
                (job_last_changed:[2022-01-01 TO *] OR 
                 job_company_name:"stealth" OR 
                 job_title:"founder" OR
                 job_title:"building" OR
                 NOT job_company_name:"{company}")
            '''
            
            params = {
                'query': query,
                'size': min(1000, limit // len(company_names)),
                'pretty': True
            }
            
            try:
                response = self.pdl_client.person.search(**params).json()
                
                if response.get('status') == 200:
                    employees = response.get('data', [])
                    all_employees.extend(employees)
                    logger.info(f"  Found {len(employees)} employees from {company}")
            except Exception as e:
                logger.error(f"Error fetching {company} employees: {e}")
        
        logger.info(f"Total employees fetched: {len(all_employees)}")
        
        # Analyze and categorize employees
        categorized = self.stealth_detector.analyze_bulk_employees(all_employees)
        
        # Save initial snapshots and set up monitoring schedules
        for tier, employees in categorized.items():
            if tier in ['vip', 'watch', 'general']:
                for emp in employees:
                    # Get full employee data
                    pdl_id = emp.get('pdl_id')
                    
                    # Find original employee data
                    original_emp = next((e for e in all_employees if e.get('id') == pdl_id), None)
                    if original_emp:
                        # Save snapshot
                        self.employment_monitor.save_snapshot(original_emp)
                        
                        # Set up monitoring schedule
                        self.employment_monitor.update_monitoring_schedule(
                            original_emp,
                            tier=emp.get('tier'),
                            stealth_score=emp.get('stealth_score'),
                            signals=emp.get('signals', [])
                        )
        
        # Log results
        logger.info("Initial categorization complete:")
        logger.info(f"  VIP (daily): {categorized['stats']['vip_count']} employees")
        logger.info(f"  Watch (weekly): {categorized['stats']['watch_count']} employees")
        logger.info(f"  General (monthly): {categorized['stats']['general_count']} employees")
        logger.info(f"  Stealth signals detected: {categorized['stats']['stealth_detected']}")
        
        return categorized
    
    def run_daily_monitoring(self) -> Dict:
        """
        Run daily monitoring routine
        Checks employees based on their tier and schedule
        """
        logger.info(f"Starting daily monitoring run at {datetime.now()}")
        
        # Get employees to check today
        employees_to_check = self.employment_monitor.get_employees_to_check_today()
        
        logger.info(f"Found {len(employees_to_check)} employees to check today")
        
        # Track results
        results = {
            'checked': 0,
            'changes_detected': [],
            'stealth_signals': [],
            'api_calls': 0,
            'cost': 0.0,
            'errors': []
        }
        
        # Process each employee
        for emp_schedule in employees_to_check:
            if results['api_calls'] >= self.daily_checks_limit:
                logger.warning(f"Reached daily limit of {self.daily_checks_limit} checks")
                break
            
            pdl_id = emp_schedule['pdl_id']
            logger.info(f"Checking {emp_schedule['full_name']} ({emp_schedule['tier']} tier)")
            
            # Fetch latest data from PDL
            current_data = self.fetch_employee_data(pdl_id)
            results['api_calls'] += 1
            results['cost'] += self.cost_per_check
            
            if not current_data:
                results['errors'].append({
                    'pdl_id': pdl_id,
                    'name': emp_schedule['full_name'],
                    'error': 'Failed to fetch data'
                })
                continue
            
            # Detect stealth signals
            stealth_score, signals, new_tier = self.stealth_detector.detect_stealth_signals(current_data)
            
            # Process update (check for changes, save snapshot, update schedule)
            update_result = self.employment_monitor.process_employee_update(
                current_data, stealth_score, signals, new_tier
            )
            
            results['checked'] += 1
            
            # Track significant findings
            if update_result['changes_detected']:
                results['changes_detected'].extend(update_result['changes_detected'])
                logger.info(f"  ⚠️ Changes detected for {emp_schedule['full_name']}")
            
            if stealth_score >= 50:
                results['stealth_signals'].append({
                    'pdl_id': pdl_id,
                    'name': emp_schedule['full_name'],
                    'score': stealth_score,
                    'signals': signals,
                    'tier': new_tier
                })
                logger.info(f"  🚀 Stealth signals detected (score: {stealth_score})")
            
            # Dynamic tier adjustment
            if new_tier != emp_schedule['tier']:
                logger.info(f"  📊 Tier changed from {emp_schedule['tier']} to {new_tier}")
        
        # Get monitoring stats
        stats = self.employment_monitor.get_monitoring_stats()
        results['stats'] = stats
        
        logger.info(f"Daily monitoring complete:")
        logger.info(f"  Checked: {results['checked']} employees")
        logger.info(f"  Changes detected: {len(results['changes_detected'])}")
        logger.info(f"  Stealth signals: {len(results['stealth_signals'])}")
        logger.info(f"  Cost: ${results['cost']:.2f}")
        
        return results
    
    def get_high_priority_alerts(self) -> List[Dict]:
        """Get recent high-priority alerts that need attention"""
        # This would query the database for unsent high-priority alerts
        # Implementation depends on alert system integration
        pass
    
    def adjust_monitoring_tier(self, pdl_id: str, new_tier: str, reason: str):
        """
        Manually adjust someone's monitoring tier
        Useful when you get external signals about someone
        """
        logger.info(f"Manually adjusting {pdl_id} to {new_tier} tier. Reason: {reason}")
        
        # Fetch current data
        current_data = self.fetch_employee_data(pdl_id)
        if current_data:
            # Re-detect signals with new tier
            stealth_score, signals, _ = self.stealth_detector.detect_stealth_signals(current_data)
            
            # Force update with new tier
            self.employment_monitor.update_monitoring_schedule(
                current_data,
                tier=new_tier,
                stealth_score=stealth_score,
                signals=signals + [f"Manual adjustment: {reason}"]
            )
            
            logger.info(f"Successfully adjusted {current_data.get('full_name')} to {new_tier} tier")
            return True
        
        return False
    
    def generate_daily_report(self, results: Dict) -> str:
        """Generate a summary report of daily monitoring"""
        report = f"""
=== Daily Monitoring Report ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 SUMMARY
- Employees Checked: {results['checked']}
- API Calls Made: {results['api_calls']}
- Total Cost: ${results['cost']:.2f}

🔔 ALERTS
- Employment Changes: {len(results['changes_detected'])}
- Stealth Signals: {len(results['stealth_signals'])}

📈 MONITORING STATS
- VIP Tier: {results['stats']['tier_distribution'].get('vip', 0)} employees
- Watch Tier: {results['stats']['tier_distribution'].get('watch', 0)} employees  
- General Tier: {results['stats']['tier_distribution'].get('general', 0)} employees
- Estimated Daily Cost: ${results['stats']['estimated_daily_cost']:.2f}

"""
        
        if results['changes_detected']:
            report += "\n🚨 TOP EMPLOYMENT CHANGES:\n"
            for change in results['changes_detected'][:5]:
                report += f"- {change['person_name']}: {change['change_type']} "
                report += f"({change['old_value']} → {change['new_value']})\n"
        
        if results['stealth_signals']:
            report += "\n🚀 TOP STEALTH SIGNALS:\n"
            for signal in sorted(results['stealth_signals'], key=lambda x: x['score'], reverse=True)[:5]:
                report += f"- {signal['name']} (Score: {signal['score']}, Tier: {signal['tier']})\n"
                report += f"  Signals: {', '.join(signal['signals'][:2])}\n"
        
        return report


def main():
    """Main execution for daily monitoring"""
    load_dotenv()
    
    # Initialize system with $5/day budget
    monitoring = TieredMonitoringSystem(daily_budget=5.0)
    
    # Check if this is first run (need initial analysis)
    stats = monitoring.employment_monitor.get_monitoring_stats()
    
    if stats['total_monitored'] == 0:
        print("No employees in monitoring system. Running initial analysis...")
        # Run initial bulk analysis (one-time setup)
        monitoring.initial_bulk_analysis(limit=5000)  # Start with 5000 employees
    
    # Run daily monitoring
    results = monitoring.run_daily_monitoring()
    
    # Generate and print report
    report = monitoring.generate_daily_report(results)
    print(report)
    
    # Save report to file
    report_path = f"data/monitoring/reports/daily_{datetime.now().strftime('%Y%m%d')}.txt"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()