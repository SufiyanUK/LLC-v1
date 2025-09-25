"""
Alert Pipeline V2 - Processes all files in updated_test folder
Automatically detects and processes all employee JSONL files
"""

import os
import sys
import json
import glob
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.alerts.three_level_alert_system import ThreeLevelAlertSystem


class AlertPipelineV2:
    """
    Enhanced pipeline that processes all files in the cache directory
    """
    
    def __init__(self):
        """Initialize the pipeline"""
        self.alert_system = ThreeLevelAlertSystem()
        self.cache_dir = 'data/raw/updated_test'
        self.output_dir = 'data/alerts'
        self.stats = {
            'files_processed': 0,
            'employees_processed': 0,
            'alerts_by_company': defaultdict(lambda: {'LEVEL_1': 0, 'LEVEL_2': 0, 'LEVEL_3': 0}),
            'total_alerts': {'LEVEL_1': 0, 'LEVEL_2': 0, 'LEVEL_3': 0}
        }
    
    def find_all_employee_files(self):
        """Find all JSONL files in the cache directory"""
        pattern = os.path.join(self.cache_dir, '*.jsonl')
        files = glob.glob(pattern)
        
        print(f"\n[SCANNING] Directory: {self.cache_dir}")
        print(f"[FOUND] {len(files)} employee data files")
        
        # Extract company names from filenames
        file_info = []
        for filepath in files:
            filename = os.path.basename(filepath)
            # Extract company name (assumes format: company_employees_*.jsonl)
            company = filename.split('_')[0] if '_' in filename else 'unknown'
            file_info.append({
                'path': filepath,
                'filename': filename,
                'company': company,
                'size': os.path.getsize(filepath) / 1024  # KB
            })
        
        return file_info
    
    def load_employees_from_file(self, filepath):
        """Load employees from a JSONL file"""
        employees = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        employees.append(json.loads(line))
            print(f"  [OK] Loaded {len(employees)} employees")
        except Exception as e:
            print(f"  [ERROR] Failed to load file: {e}")
        
        return employees
    
    def process_all_files(self, specific_file=None):
        """
        Process all files or a specific file
        
        Args:
            specific_file: Optional filename to process only that file
        """
        print("\n" + "="*80)
        print("[RUNNING] ALERT PIPELINE V2 - MULTI-FILE PROCESSOR")
        print("="*80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Find all files
        file_info = self.find_all_employee_files()
        
        if not file_info:
            print("[WARNING] No employee files found in cache directory")
            return None
        
        # Filter for specific file if provided
        if specific_file:
            file_info = [f for f in file_info if f['filename'] == specific_file]
            if not file_info:
                print(f"[ERROR] File '{specific_file}' not found")
                return None
        
        # Process each file
        all_results = {
            'LEVEL_1': [],
            'LEVEL_2': [],
            'LEVEL_3': [],
            'by_company': defaultdict(lambda: {'LEVEL_1': [], 'LEVEL_2': [], 'LEVEL_3': []})
        }
        
        print(f"\n[PROCESSING] {len(file_info)} files")
        print("-"*60)
        
        for i, file_data in enumerate(file_info, 1):
            print(f"\n[FILE {i}/{len(file_info)}] {file_data['filename']}")
            print(f"  Company: {file_data['company'].upper()}")
            print(f"  Size: {file_data['size']:.2f} KB")
            
            # Load employees from file
            employees = self.load_employees_from_file(file_data['path'])
            
            if not employees:
                print("  [SKIP] No employees to process")
                continue
            
            # Process employees to add required fields
            print(f"  [PROCESSING] Analyzing {len(employees)} employees...")
            
            # Import processing functions
            from src.data_processing.employee_processor import (
                extract_location, get_current_company, get_previous_companies,
                get_last_role, get_last_big_tech_departure, extract_education
            )
            from config.companies import AI_FOCUSED_BIG_TECH
            
            # Process each employee to add the required fields
            processed_employees = []
            for emp in employees:
                processed = {
                    'pdl_id': emp.get('id'),
                    'full_name': emp.get('full_name'),
                    'first_name': emp.get('first_name'),
                    'last_name': emp.get('last_name'),
                    'location': extract_location(emp),
                    'current_company': get_current_company(emp),
                    'previous_companies': get_previous_companies(emp),
                    'last_known_role': get_last_role(emp),
                    'last_big_tech_departure': get_last_big_tech_departure(emp, AI_FOCUSED_BIG_TECH),
                    'linkedin_url': emp.get('linkedin_url'),
                    'skills': emp.get('skills', []),
                    'education': extract_education(emp),
                    'experience': emp.get('experience', []),
                    
                    # Include raw fields needed for alert detection
                    'job_company_name': emp.get('job_company_name'),
                    'job_title': emp.get('job_title'),
                    'job_company_size': emp.get('job_company_size'),
                    'job_last_changed': emp.get('job_last_changed'),
                    'job_last_updated': emp.get('job_last_updated'),
                    'job_title_role': emp.get('job_title_role'),
                    'job_title_sub_role': emp.get('job_title_sub_role'),
                    'summary': emp.get('summary'),
                    'headline': emp.get('headline')
                }
                processed_employees.append(processed)
            
            # Now analyze the processed employees
            results = self.alert_system.analyze_employees(processed_employees)
            
            # Update statistics
            self.stats['files_processed'] += 1
            self.stats['employees_processed'] += len(employees)
            
            # Aggregate results
            company = file_data['company']
            for level in ['LEVEL_1', 'LEVEL_2', 'LEVEL_3']:
                alerts = results.get(level, [])
                if alerts:
                    all_results[level].extend(alerts)
                    all_results['by_company'][company][level].extend(alerts)
                    self.stats['alerts_by_company'][company][level] += len(alerts)
                    self.stats['total_alerts'][level] += len(alerts)
            
            # Show file-specific results
            total_file_alerts = sum(len(results.get(level, [])) for level in ['LEVEL_1', 'LEVEL_2', 'LEVEL_3'])
            print(f"  [RESULTS] Generated {total_file_alerts} alerts")
            print(f"    - Level 3 (Immediate): {len(results.get('LEVEL_3', []))}")
            print(f"    - Level 2 (High Priority): {len(results.get('LEVEL_2', []))}")
            print(f"    - Level 1 (Monitoring): {len(results.get('LEVEL_1', []))}")
        
        return all_results
    
    def display_summary(self, results):
        """Display comprehensive summary of all results"""
        print("\n" + "="*80)
        print("[SUMMARY] ALERT PIPELINE V2 RESULTS")
        print("="*80)
        
        # Overall statistics
        print(f"\n[STATISTICS]")
        print(f"  Files Processed: {self.stats['files_processed']}")
        print(f"  Total Employees: {self.stats['employees_processed']}")
        print(f"  Total Alerts: {sum(self.stats['total_alerts'].values())}")
        
        # Alerts by level
        print(f"\n[ALERTS BY LEVEL]")
        print(f"  Level 3 (Immediate Action): {self.stats['total_alerts']['LEVEL_3']}")
        print(f"  Level 2 (High Priority): {self.stats['total_alerts']['LEVEL_2']}")
        print(f"  Level 1 (Monitoring): {self.stats['total_alerts']['LEVEL_1']}")
        
        # Alerts by company
        print(f"\n[ALERTS BY COMPANY]")
        for company, levels in sorted(self.stats['alerts_by_company'].items()):
            total = sum(levels.values())
            if total > 0:
                print(f"  {company.upper()}: {total} alerts")
                print(f"    - L3: {levels['LEVEL_3']}, L2: {levels['LEVEL_2']}, L1: {levels['LEVEL_1']}")
        
        # High priority alerts detail
        high_priority = []
        for alert in results['LEVEL_3']:
            if alert:
                high_priority.append(('LEVEL_3', alert))
        for alert in results['LEVEL_2']:
            if alert:
                high_priority.append(('LEVEL_2', alert))
        
        if high_priority:
            print(f"\n[HIGH PRIORITY ALERTS] ({len(high_priority)} total)")
            print("-"*60)
            for level, alert in high_priority[:10]:  # Show top 10
                print(f"  [{level}] {alert.get('full_name', 'Unknown')}")
                if alert.get('departure_info'):
                    print(f"    From: {alert['departure_info'].get('company', 'Unknown')}")
                if alert.get('building_phrases'):
                    print(f"    Signals: {', '.join(alert['building_phrases'][:3])}")
                print(f"    Priority Score: {alert.get('priority_score', 0):.1f}")
                print()
    
    def save_results(self, results):
        """Save all results to files"""
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save complete results
        full_path = os.path.join(self.output_dir, f'alerts_v2_full_{timestamp}.json')
        with open(full_path, 'w', encoding='utf-8') as f:
            output_data = {
                'version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'stats': {
                    'files_processed': self.stats['files_processed'],
                    'employees_processed': self.stats['employees_processed'],
                    'total_alerts': sum(self.stats['total_alerts'].values()),
                    'level_3_count': self.stats['total_alerts']['LEVEL_3'],
                    'level_2_count': self.stats['total_alerts']['LEVEL_2'],
                    'level_1_count': self.stats['total_alerts']['LEVEL_1'],
                    'by_company': dict(self.stats['alerts_by_company'])
                },
                'LEVEL_3': results['LEVEL_3'],
                'LEVEL_2': results['LEVEL_2'],
                'LEVEL_1': results['LEVEL_1'],
                'by_company': dict(results['by_company'])
            }
            json.dump(output_data, f, indent=2, default=str)
        
        # Save high-priority alerts separately
        priority_path = os.path.join(self.output_dir, f'alerts_v2_high_priority_{timestamp}.json')
        with open(priority_path, 'w', encoding='utf-8') as f:
            priority_data = {
                'timestamp': datetime.now().isoformat(),
                'LEVEL_3': results['LEVEL_3'],
                'LEVEL_2': results['LEVEL_2'],
                'total_high_priority': len(results['LEVEL_3']) + len(results['LEVEL_2'])
            }
            json.dump(priority_data, f, indent=2, default=str)
        
        # Save CSV for easy viewing
        csv_path = os.path.join(self.output_dir, f'alerts_v2_summary_{timestamp}.csv')
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('Level,Name,Previous Company,Current,Building Signals,Founder Score,Stealth Score,Priority\n')
            
            for level in ['LEVEL_3', 'LEVEL_2', 'LEVEL_1']:
                for alert in results[level]:
                    if alert:
                        name = alert.get('full_name', '')
                        prev = alert.get('departure_info', {}).get('company', '') if alert.get('departure_info') else ''
                        current = alert.get('job_company_name', '')
                        phrases = '|'.join(alert.get('building_phrases', []))
                        founder = alert.get('founder_score', 0)
                        stealth = alert.get('stealth_score', 0)
                        priority = alert.get('priority_score', 0)
                        f.write(f'{level},"{name}","{prev}","{current}","{phrases}",{founder:.1f},{stealth},{priority:.1f}\n')
        
        print(f"\n[SAVED] Results to:")
        print(f"  - Full results: {full_path}")
        print(f"  - High priority: {priority_path}")
        print(f"  - CSV summary: {csv_path}")
        
        return full_path
    
    def run(self, specific_file=None):
        """
        Main pipeline execution
        
        Args:
            specific_file: Optional - process only this file
        """
        # Process files
        results = self.process_all_files(specific_file)
        
        if not results:
            print("[ERROR] No results generated")
            return None
        
        # Display summary
        self.display_summary(results)
        
        # Save results
        output_path = self.save_results(results)
        
        print("\n" + "="*80)
        print("[SUCCESS] ALERT PIPELINE V2 COMPLETED")
        print("="*80)
        
        return results


def main():
    """Main function"""
    
    # Initialize pipeline
    pipeline = AlertPipelineV2()
    
    # Check for command line arguments
    specific_file = None
    if len(sys.argv) > 1:
        specific_file = sys.argv[1]
        print(f"\n[MODE] Processing specific file: {specific_file}")
    else:
        print("\n[MODE] Processing ALL files in cache directory")
        print("[TIP] You can process a specific file by running:")
        print("      python run_alert_pipeline_v2.py <filename.jsonl>")
    
    # Run the pipeline
    results = pipeline.run(specific_file)
    
    # Show actionable summary
    if results:
        total_high_priority = len(results['LEVEL_3']) + len(results['LEVEL_2'])
        if total_high_priority > 0:
            print(f"\n[ACTION REQUIRED]")
            print(f"{total_high_priority} high-priority alerts need immediate attention!")
            print("Review the high_priority JSON file for details.")


if __name__ == "__main__":
    main()