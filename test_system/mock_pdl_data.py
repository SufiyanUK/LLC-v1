"""
Mock PDL Data for Testing Departure Detection and Alert System
Simulates PDL API responses without using credits
"""

from datetime import datetime, timedelta

class MockPDLData:
    """Mock PDL API responses for testing"""
    
    def __init__(self):
        # Base timestamp for consistency
        self.now = datetime.now()
        self.three_months_ago = (self.now - timedelta(days=90)).isoformat()
        self.one_month_ago = (self.now - timedelta(days=30)).isoformat()
        
    def get_test_employees(self):
        """Get initial employees at big tech companies"""
        return [
            # Test Case 1: Will move to another big tech (Level 1)
            {
                'id': 'test_pdl_001',
                'full_name': 'John Smith',
                'job_title': 'Senior Software Engineer',
                'job_company_name': 'OpenAI',
                'job_company_size': '500-1000',
                'job_company_type': 'technology',
                'job_title_levels': ['senior'],
                'linkedin_url': 'linkedin.com/in/johnsmith',
                'headline': 'Senior Software Engineer at OpenAI',
                'summary': 'Building cutting-edge AI systems at OpenAI',
                'job_last_changed': self.three_months_ago,
                '_test_scenario': 'level_1_departure'
            },
            
            # Test Case 2: Will show "building" signals (Level 2)
            {
                'id': 'test_pdl_002',
                'full_name': 'Sarah Johnson',
                'job_title': 'Staff Machine Learning Engineer',
                'job_company_name': 'Anthropic',
                'job_company_size': '100-500',
                'job_company_type': 'artificial intelligence',
                'job_title_levels': ['staff'],
                'linkedin_url': 'linkedin.com/in/sarahjohnson',
                'headline': 'Staff ML Engineer at Anthropic',
                'summary': 'Passionate about AGI safety and alignment',
                'job_last_changed': self.three_months_ago,
                '_test_scenario': 'level_2_building'
            },
            
            # Test Case 3: Will join a startup (Level 3)
            {
                'id': 'test_pdl_003',
                'full_name': 'Michael Chen',
                'job_title': 'Principal Engineer',
                'job_company_name': 'Meta',
                'job_company_size': '10000+',
                'job_company_type': 'technology',
                'job_title_levels': ['principal'],
                'linkedin_url': 'linkedin.com/in/michaelchen',
                'headline': 'Principal Engineer at Meta',
                'summary': 'Leading infrastructure teams at Meta',
                'job_last_changed': self.three_months_ago,
                '_test_scenario': 'level_3_startup'
            },
            
            # Test Case 4: Stealth mode (Level 3)
            {
                'id': 'test_pdl_004',
                'full_name': 'Emily Rodriguez',
                'job_title': 'Director of Engineering',
                'job_company_name': 'Google',
                'job_company_size': '10000+',
                'job_company_type': 'technology',
                'job_title_levels': ['director'],
                'linkedin_url': 'linkedin.com/in/emilyrodriguez',
                'headline': 'Director of Engineering at Google',
                'summary': 'Building world-class products at Google',
                'job_last_changed': self.three_months_ago,
                '_test_scenario': 'level_3_stealth'
            },
            
            # Test Case 5: No departure (stays at company)
            {
                'id': 'test_pdl_005',
                'full_name': 'David Kim',
                'job_title': 'Senior Research Scientist',
                'job_company_name': 'DeepMind',
                'job_company_size': '1000-5000',
                'job_company_type': 'artificial intelligence',
                'job_title_levels': ['senior'],
                'linkedin_url': 'linkedin.com/in/davidkim',
                'headline': 'Senior Research Scientist at DeepMind',
                'summary': 'Advancing AI research at DeepMind',
                'job_last_changed': self.three_months_ago,
                '_test_scenario': 'no_departure'
            }
        ]
    
    def get_departure_checks(self):
        """Get updated employee data simulating departures"""
        return {
            # Level 1: Moved to Microsoft (big tech to big tech)
            'test_pdl_001': {
                'id': 'test_pdl_001',
                'full_name': 'John Smith',
                'job_title': 'Principal Software Engineer',
                'job_company_name': 'Microsoft',  # Changed company
                'job_company_size': '10000+',
                'job_company_type': 'technology',
                'job_title_levels': ['principal'],
                'linkedin_url': 'linkedin.com/in/johnsmith',
                'headline': 'Principal Software Engineer at Microsoft',
                'summary': 'Excited to join the Azure team at Microsoft',
                'job_last_changed': self.one_month_ago,
                'job_company_founded': '1975',
                'job_company_industry': 'Software Development'
            },
            
            # Level 2: Left with "building" signals
            'test_pdl_002': {
                'id': 'test_pdl_002',
                'full_name': 'Sarah Johnson',
                'job_title': 'Founder',
                'job_company_name': 'Stealth Startup',  # Vague company
                'job_company_size': '',  # Unknown size
                'job_company_type': '',
                'job_title_levels': [],
                'linkedin_url': 'linkedin.com/in/sarahjohnson',
                'headline': 'Working on something new in the AI space | Ex-Anthropic',  # Building signal
                'summary': 'After amazing years at Anthropic, I\'m building something exciting in stealth mode. Stay tuned!',
                'job_last_changed': self.one_month_ago,
                'job_company_founded': '',
                'job_company_industry': ''
            },
            
            # Level 3: Joined a startup
            'test_pdl_003': {
                'id': 'test_pdl_003',
                'full_name': 'Michael Chen',
                'job_title': 'CTO & Co-Founder',
                'job_company_name': 'NeuralTech AI',  # Startup name
                'job_company_size': '11-50',  # Small company
                'job_company_type': 'startup',
                'job_title_levels': ['cto'],
                'linkedin_url': 'linkedin.com/in/michaelchen',
                'headline': 'CTO & Co-Founder at NeuralTech AI | Building the future of AI assistants',
                'summary': 'Excited to announce I\'ve co-founded NeuralTech AI! We\'re building next-gen AI assistants.',
                'job_last_changed': self.one_month_ago,
                'job_company_founded': '2024',  # Recent founding
                'job_company_industry': 'Artificial Intelligence'
            },
            
            # Level 3: Stealth mode
            'test_pdl_004': {
                'id': 'test_pdl_004',
                'full_name': 'Emily Rodriguez',
                'job_title': 'CEO',
                'job_company_name': '',  # No company = stealth
                'job_company_size': '',
                'job_company_type': '',
                'job_title_levels': ['ceo'],
                'linkedin_url': 'linkedin.com/in/emilyrodriguez',
                'headline': 'Building in stealth | Previously Director at Google',
                'summary': 'After 8 incredible years at Google, I\'m starting something new. Can\'t share details yet but very excited!',
                'job_last_changed': self.one_month_ago,
                'job_company_founded': '',
                'job_company_industry': ''
            },
            
            # No departure - still at DeepMind
            'test_pdl_005': {
                'id': 'test_pdl_005',
                'full_name': 'David Kim',
                'job_title': 'Senior Research Scientist',
                'job_company_name': 'DeepMind',  # Same company
                'job_company_size': '1000-5000',
                'job_company_type': 'artificial intelligence',
                'job_title_levels': ['senior'],
                'linkedin_url': 'linkedin.com/in/davidkim',
                'headline': 'Senior Research Scientist at DeepMind',
                'summary': 'Advancing AI research at DeepMind',
                'job_last_changed': self.three_months_ago,
                'job_company_founded': '2010',
                'job_company_industry': 'Artificial Intelligence Research'
            }
        }
    
    def get_expected_results(self):
        """Expected classification results for validation"""
        return {
            'test_pdl_001': {
                'departure': True,
                'alert_level': 1,
                'reason': 'Moved from OpenAI to Microsoft (big tech to big tech)'
            },
            'test_pdl_002': {
                'departure': True,
                'alert_level': 2,
                'reason': 'Has "working on something new" signals, stealth mode'
            },
            'test_pdl_003': {
                'departure': True,
                'alert_level': 3,
                'reason': 'Joined startup (11-50 employees, founded 2024)'
            },
            'test_pdl_004': {
                'departure': True,
                'alert_level': 3,
                'reason': 'CEO/Founder in stealth (no company name)'
            },
            'test_pdl_005': {
                'departure': False,
                'alert_level': 0,
                'reason': 'Still at DeepMind'
            }
        }