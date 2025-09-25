"""
Employment Change Monitoring System
Tracks changes in employment status and sends alerts
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import hashlib
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmploymentChange:
    """Represents a detected employment change"""
    pdl_id: str
    person_name: str
    change_type: str  # 'job_title', 'company', 'departure', 'stealth_signal'
    old_value: str
    new_value: str
    confidence: float
    detected_at: str
    details: Dict

class EmploymentMonitor:
    """
    Monitors employment changes and manages the tiered checking system
    """
    
    def __init__(self, db_path: str = "data/monitoring/employment_history.db"):
        self.db_path = db_path
        self.init_database()
        
        # Alert thresholds
        self.ALERT_TYPES = {
            'DEPARTURE_NO_NEW_ROLE': {
                'priority': 'high',
                'description': 'Employee left company without new role'
            },
            'JOB_TITLE_CHANGE': {
                'priority': 'medium',
                'description': 'Job title updated'
            },
            'STEALTH_COMPANY': {
                'priority': 'high',
                'description': 'Joined company with stealth indicators'
            },
            'BUILDING_SOMETHING': {
                'priority': 'high',
                'description': 'Profile indicates building/founding activity'
            },
            'COMPANY_CHANGE': {
                'priority': 'medium',
                'description': 'Changed companies'
            }
        }
    
    def init_database(self):
        """Initialize SQLite database for tracking"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for employment snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employment_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdl_id TEXT NOT NULL,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                full_name TEXT,
                job_company_name TEXT,
                job_title TEXT,
                job_company_size TEXT,
                job_last_changed TEXT,
                experience_json TEXT,
                data_hash TEXT,
                UNIQUE(pdl_id, data_hash)
            )
        ''')
        
        # Table for detected changes/alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                pdl_id TEXT NOT NULL,
                person_name TEXT,
                old_value TEXT,
                new_value TEXT,
                confidence REAL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Table for monitoring schedule
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_schedule (
                pdl_id TEXT PRIMARY KEY,
                full_name TEXT,
                tier TEXT NOT NULL,
                stealth_score REAL,
                last_checked TIMESTAMP,
                next_check TIMESTAMP,
                check_frequency TEXT,
                signals TEXT,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def compute_data_hash(self, employee: Dict) -> str:
        """Compute hash of relevant employment data to detect changes"""
        # Validate input
        if not employee or not isinstance(employee, dict):
            return hashlib.md5(b"empty").hexdigest()
        
        relevant_fields = {
            'job_company_name': str(employee.get('job_company_name', '')),
            'job_title': str(employee.get('job_title', '')),
            'job_company_size': str(employee.get('job_company_size', '')),
            'is_primary_experience': str(self._get_primary_experience(employee))
        }
        
        hash_string = json.dumps(relevant_fields, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _get_primary_experience(self, employee: Dict) -> Dict:
        """Extract primary (current) experience"""
        if not employee or not isinstance(employee, dict):
            return {}
        
        experiences = employee.get('experience', [])
        if experiences and isinstance(experiences, list):
            for exp in experiences:
                if isinstance(exp, dict) and exp.get('is_primary'):
                    return exp
        return {}
    
    def save_snapshot(self, employee: Dict) -> bool:
        """Save employment snapshot to database"""
        # Validate input
        if not employee or not isinstance(employee, dict):
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data_hash = self.compute_data_hash(employee)
        
        try:
            cursor.execute('''
                INSERT INTO employment_snapshots 
                (pdl_id, full_name, job_company_name, job_title, 
                 job_company_size, job_last_changed, experience_json, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee.get('id'),
                employee.get('full_name'),
                employee.get('job_company_name'),
                employee.get('job_title'),
                employee.get('job_company_size'),
                employee.get('job_last_changed'),
                json.dumps(employee.get('experience', [])),
                data_hash
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Same data hash - no changes
            conn.close()
            return False
    
    def get_last_snapshot(self, pdl_id: str) -> Optional[Dict]:
        """Get most recent snapshot for a person"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM employment_snapshots 
            WHERE pdl_id = ?
            ORDER BY snapshot_date DESC
            LIMIT 1
        ''', (pdl_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'pdl_id': row[1],
                'snapshot_date': row[2],
                'full_name': row[3],
                'job_company_name': row[4],
                'job_title': row[5],
                'job_company_size': row[6],
                'job_last_changed': row[7],
                'experience': json.loads(row[8]) if row[8] else [],
                'data_hash': row[9]
            }
        return None
    
    def detect_changes(self, current: Dict, historical: Optional[Dict]) -> List[EmploymentChange]:
        """Detect employment changes between snapshots"""
        changes = []
        
        if not historical:
            # First time seeing this person
            return changes
        
        # Check job title change
        if current.get('job_title') != historical.get('job_title'):
            change = EmploymentChange(
                pdl_id=current.get('id'),
                person_name=current.get('full_name'),
                change_type='job_title',
                old_value=historical.get('job_title', ''),
                new_value=current.get('job_title', ''),
                confidence=0.9,
                detected_at=datetime.now().isoformat(),
                details={'job_company': current.get('job_company_name')}
            )
            changes.append(change)
            
            # Check for stealth signals in new title
            new_title_lower = (current.get('job_title', '') or '').lower()
            if any(signal in new_title_lower for signal in ['building', 'founder', 'stealth', 'working on']):
                change = EmploymentChange(
                    pdl_id=current.get('id'),
                    person_name=current.get('full_name'),
                    change_type='stealth_signal',
                    old_value='',
                    new_value=f"Title changed to: {current.get('job_title')}",
                    confidence=0.85,
                    detected_at=datetime.now().isoformat(),
                    details={'signal_type': 'title_change', 'title': current.get('job_title')}
                )
                changes.append(change)
        
        # Check company change
        if current.get('job_company_name') != historical.get('job_company_name'):
            old_company = historical.get('job_company_name', '')
            new_company = current.get('job_company_name', '')
            
            # Departure without new role
            if old_company and not new_company:
                change = EmploymentChange(
                    pdl_id=current.get('id'),
                    person_name=current.get('full_name'),
                    change_type='departure',
                    old_value=old_company,
                    new_value='No company listed',
                    confidence=0.95,
                    detected_at=datetime.now().isoformat(),
                    details={'left_company': old_company}
                )
                changes.append(change)
            
            # Joined new company
            elif new_company:
                change = EmploymentChange(
                    pdl_id=current.get('id'),
                    person_name=current.get('full_name'),
                    change_type='company_change',
                    old_value=old_company,
                    new_value=new_company,
                    confidence=0.9,
                    detected_at=datetime.now().isoformat(),
                    details={'from': old_company, 'to': new_company}
                )
                changes.append(change)
                
                # Check if new company is stealth
                new_company_lower = new_company.lower()
                if any(signal in new_company_lower for signal in ['stealth', 'building', 'consulting', 'advisor']):
                    change = EmploymentChange(
                        pdl_id=current.get('id'),
                        person_name=current.get('full_name'),
                        change_type='stealth_company',
                        old_value=old_company,
                        new_value=new_company,
                        confidence=0.8,
                        detected_at=datetime.now().isoformat(),
                        details={'stealth_company': new_company}
                    )
                    changes.append(change)
        
        return changes
    
    def save_alert(self, change: EmploymentChange):
        """Save alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts 
            (alert_type, pdl_id, person_name, old_value, new_value, 
             confidence, details, sent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            change.change_type,
            change.pdl_id,
            change.person_name,
            change.old_value,
            change.new_value,
            change.confidence,
            json.dumps(change.details),
            False
        ))
        
        conn.commit()
        conn.close()
    
    def update_monitoring_schedule(self, employee: Dict, tier: str, stealth_score: float, signals: List[str]):
        """Update or create monitoring schedule for employee"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine next check based on tier
        frequencies = {
            'vip': {'days': 1, 'label': 'daily'},
            'watch': {'days': 7, 'label': 'weekly'},
            'general': {'days': 30, 'label': 'monthly'}
        }
        
        freq = frequencies.get(tier, frequencies['general'])
        next_check = datetime.now() + timedelta(days=freq['days'])
        
        cursor.execute('''
            INSERT OR REPLACE INTO monitoring_schedule
            (pdl_id, full_name, tier, stealth_score, last_checked, 
             next_check, check_frequency, signals, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            employee.get('id'),
            employee.get('full_name'),
            tier,
            stealth_score,
            datetime.now(),
            next_check,
            freq['label'],
            json.dumps(signals),
            True
        ))
        
        conn.commit()
        conn.close()
    
    def get_employees_to_check_today(self) -> List[Dict]:
        """Get list of employees that need checking today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pdl_id, full_name, tier, stealth_score, signals
            FROM monitoring_schedule
            WHERE next_check <= ? AND active = TRUE
            ORDER BY tier ASC, stealth_score DESC
        ''', (datetime.now(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        employees_to_check = []
        for row in rows:
            employees_to_check.append({
                'pdl_id': row[0],
                'full_name': row[1],
                'tier': row[2],
                'stealth_score': row[3],
                'signals': json.loads(row[4]) if row[4] else []
            })
        
        return employees_to_check
    
    def get_monitoring_stats(self) -> Dict:
        """Get statistics about monitoring"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count by tier
        cursor.execute('''
            SELECT tier, COUNT(*) 
            FROM monitoring_schedule 
            WHERE active = TRUE
            GROUP BY tier
        ''')
        tier_counts = dict(cursor.fetchall())
        
        # Recent alerts
        cursor.execute('''
            SELECT COUNT(*) 
            FROM alerts 
            WHERE created_at > datetime('now', '-7 days')
        ''')
        recent_alerts = cursor.fetchone()[0]
        
        # Unsent alerts
        cursor.execute('''
            SELECT COUNT(*) 
            FROM alerts 
            WHERE sent = FALSE
        ''')
        unsent_alerts = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'tier_distribution': tier_counts,
            'recent_alerts_7d': recent_alerts,
            'unsent_alerts': unsent_alerts,
            'total_monitored': sum(tier_counts.values()),
            'estimated_daily_cost': (
                tier_counts.get('vip', 0) * 0.01 +  # Daily
                tier_counts.get('watch', 0) * 0.01 / 7 +  # Weekly
                tier_counts.get('general', 0) * 0.01 / 30  # Monthly
            )
        }
    
    def process_employee_update(self, current_employee: Dict, stealth_score: float, 
                               signals: List[str], tier: str) -> Dict:
        """
        Process an employee update - check for changes and update schedule
        
        Returns dict with changes detected and actions taken
        """
        result = {
            'pdl_id': current_employee.get('id'),
            'name': current_employee.get('full_name'),
            'changes_detected': [],
            'new_snapshot': False,
            'tier_updated': False
        }
        
        # Get historical snapshot
        historical = self.get_last_snapshot(current_employee.get('id'))
        
        # Detect changes
        changes = self.detect_changes(current_employee, historical)
        
        # Save alerts for changes
        for change in changes:
            self.save_alert(change)
            result['changes_detected'].append(asdict(change))
        
        # Save new snapshot if data changed
        if self.save_snapshot(current_employee):
            result['new_snapshot'] = True
        
        # Update monitoring schedule
        self.update_monitoring_schedule(current_employee, tier, stealth_score, signals)
        result['tier_updated'] = True
        result['current_tier'] = tier
        result['stealth_score'] = stealth_score
        
        return result