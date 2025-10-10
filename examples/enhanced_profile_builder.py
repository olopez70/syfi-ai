#!/usr/bin/env python3
"""
Enhanced ProfileBuilder for Entity-Specific Banking Patterns

This enhanced version analyzes ProfileTemplate descriptions and generates
banking patterns that match the actual entity type (family, business, non-profit, etc.)
instead of always generating family-style patterns.
"""

import sys
import os
from pathlib import Path
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import re

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.syfi.models.profile import Profile, ProfileTemplate, TransactionProfile
from src.syfi.models.account import AccountType
import re

# Note: Imports added above - removed duplicate imports


class EntityAnalyzer:
    """Analyzes profile descriptions to determine entity type and characteristics."""
    
    ENTITY_PATTERNS = {
        'family': [
            r'family', r'household', r'suburban', r'children', r'spouse', r'married',
            r'mortgage', r'childcare', r'homeowner', r'parents'
        ],
        'restaurant': [
            r'restaurant', r'dining', r'food service', r'kitchen', r'menu', r'chef',
            r'server', r'dine-in', r'takeout', r'delivery', r'hospitality', r'italian',
            r'bistro', r'cafe', r'grill', r'eatery', r'lunch', r'dinner'
        ],
        'retail': [
            r'supermarket', r'grocery', r'store', r'retail', r'shopping', r'merchandise',
            r'inventory', r'customers', r'sales', r'cashier', r'checkout'
        ],
        'nonprofit': [
            r'non-profit', r'nonprofit', r'foundation', r'charity', r'community',
            r'grants', r'donations', r'volunteers', r'programs', r'social'
        ],
        'professional_services': [
            r'consulting', r'legal', r'accounting', r'medical', r'dental', r'clinic',
            r'office', r'practice', r'clients', r'professional'
        ],
        'manufacturing': [
            r'factory', r'manufacturing', r'production', r'warehouse', r'assembly',
            r'industrial', r'machinery', r'workers', r'shifts'
        ]
    }
    
    @classmethod
    def analyze_entity_type(cls, description: str) -> Dict[str, Any]:
        """Analyze description to determine entity type and characteristics."""
        description_lower = description.lower()
        
        # Score each entity type
        entity_scores = {}
        for entity_type, patterns in cls.ENTITY_PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, description_lower))
            if score > 0:
                entity_scores[entity_type] = score
        
        # Determine primary entity type
        if not entity_scores:
            entity_type = 'family'  # Default fallback
        else:
            entity_type = max(entity_scores.keys(), key=lambda k: entity_scores[k])
        
        # Extract revenue/income indicators
        income_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|k|thousand)?', description)
        revenue_range = None
        if income_match:
            amount_str = income_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'million' in income_match.group(0).lower():
                revenue_range = (int(amount * 1000000 * 0.8), int(amount * 1000000 * 1.2))
            elif 'k' in income_match.group(0).lower() or 'thousand' in income_match.group(0).lower():
                revenue_range = (int(amount * 1000 * 0.8), int(amount * 1000 * 1.2))
            else:
                revenue_range = (int(amount * 0.8), int(amount * 1.2))
        
        # Extract size indicators
        size_indicators = {
            'small': re.search(r'small|local|family-owned|independent', description_lower),
            'medium': re.search(r'medium|regional|established', description_lower), 
            'large': re.search(r'large|major|enterprise|corporate', description_lower)
        }
        
        size = 'medium'  # Default
        for size_type, match in size_indicators.items():
            if match:
                size = size_type
                break
        
        return {
            'entity_type': entity_type,
            'size': size,
            'revenue_range': revenue_range,
            'description': description,
            'confidence_scores': entity_scores
        }


class EnhancedProfileBuilder:
    """Enhanced ProfileBuilder that creates entity-specific banking patterns."""
    
    def __init__(self, db_manager=None, seed: Optional[int] = None):
        self.db_manager = db_manager
        self.seed = seed or random.randint(1000, 9999)
        self.analyzer = EntityAnalyzer()
        self.profile_counter = 0  # Counter to ensure unique names
    
    def save_profile_template(self, template: ProfileTemplate, analysis: Dict[str, Any]) -> str:
        """Save profile template to database with enhanced entity-specific info."""
        if not self.db_manager:
            return template.template_id  # Skip if no database manager
            
        # Map entity types to display values
        entity_type_map = {
            'family': 'personal',
            'restaurant': 'business', 
            'retail': 'business',
            'nonprofit': 'non-profit'
        }
        
        category_map = {
            'family': 'Personal',
            'restaurant': 'Business',
            'retail': 'Business', 
            'nonprofit': 'Non-profit'
        }
        
        # Determine icons and colors
        icon_map = {
            'family': '🏠',
            'restaurant': '🍽️',
            'retail': '🛒',
            'nonprofit': '❤️'
        }
        
        color_map = {
            'family': 'primary',
            'restaurant': 'success',
            'retail': 'warning',
            'nonprofit': 'info'
        }
        
        entity_type = analysis['entity_type']
        
        # Get entity-specific account and transaction types
        accounts, transactions = self._get_entity_banking_patterns(entity_type)
        
        # Determine income range
        income_range = "$50k - $150k"  # Default
        if analysis.get('revenue_range'):
            min_val, max_val = analysis['revenue_range']
            if max_val >= 1000000:
                income_range = f"${min_val//1000}k - ${max_val//1000000}M"
            else:
                income_range = f"${min_val//1000}k - ${max_val//1000}k"
        
        return self.db_manager.insert_profile_template(
            template_id=template.template_id,
            name=template.name,
            description=template.description,
            entity_type=entity_type_map.get(entity_type, 'personal'),
            category=category_map.get(entity_type, 'Personal'),
            complexity_level=analysis.get('size', 'Medium').capitalize(),
            icon=icon_map.get(entity_type, '🏠'),
            color=color_map.get(entity_type, 'primary'),
            typical_income_range=income_range,
            typical_accounts=accounts,
            typical_transactions=transactions,
            tags=getattr(template, 'tags', []),
            metadata={'analysis': analysis}
        )
    
    def _get_entity_banking_patterns(self, entity_type: str) -> tuple:
        """Get typical accounts and transactions for entity type."""
        patterns = {
            'family': (
                ["Checking Account", "Savings Account", "Credit Card", "Mortgage Account"],
                ["Salary deposits", "Bill payments", "Grocery purchases", "Entertainment", "Mortgage payments"]
            ),
            'restaurant': (
                ["Business Checking", "Business Savings", "Equipment Loan", "Line of Credit"],
                ["Daily revenue", "Supplier payments", "Staff payroll", "Equipment purchases", "Lease payments"]
            ),
            'retail': (
                ["Business Checking", "Merchant Account", "Inventory Financing", "Business Credit"],
                ["Sales revenue", "Inventory purchases", "Vendor payments", "Payroll", "Utilities"]
            ),
            'nonprofit': (
                ["Operating Account", "Grant Account", "Restricted Funds", "Endowment Account"], 
                ["Grant deposits", "Program expenses", "Administrative costs", "Fundraising events", "Donor contributions"]
            )
        }
        return patterns.get(entity_type, patterns['family'])
    
    def _save_profile_to_database(self, profile: Profile, analysis: Dict[str, Any]) -> str:
        """Save profile instance to database."""
        if not self.db_manager:
            return profile.profile_id
            
        return self.db_manager.insert_profile(
            profile_id=profile.profile_id,
            template_id=profile.template_id,
            name=profile.name,
            description=profile.description,
            parameters={
                "entity_type": analysis.get('entity_type', 'family'),
                "size": analysis.get('size', 'medium'),
                "revenue_range": analysis.get('revenue_range'),
                "generation_seed": profile.generation_seed
            },
            metadata={'analysis': analysis}
        )

    def build_profile(self, template: ProfileTemplate, profile_name: str, **kwargs) -> Profile:
        """Build entity-specific profile based on template analysis."""
        # Increment counter for unique naming
        self.profile_counter += 1
        
        # Use base seed plus counter to ensure uniqueness
        profile_seed = self.seed + self.profile_counter * 1000
        random.seed(profile_seed)
        
        # Analyze the template to determine entity type
        analysis = self.analyzer.analyze_entity_type(template.description)
        
        # Save template to database if database manager available
        if self.db_manager:
            self.save_profile_template(template, analysis)
        
        # Create base profile
        profile = Profile(
            template_id=template.template_id,
            name=profile_name,
            description=f"Generated from template: {template.name}",
            generation_seed=profile_seed
        )
        
        # Save profile to database if database manager available
        if self.db_manager:
            self._save_profile_to_database(profile, analysis)
        
        # Generate entity-specific data based on analysis
        entity_type = analysis['entity_type']
        
        if entity_type == 'family':
            self._generate_family_profile(profile, template, analysis)
        elif entity_type == 'restaurant':
            self._generate_restaurant_profile(profile, template, analysis)
        elif entity_type == 'retail':
            self._generate_retail_profile(profile, template, analysis)
        elif entity_type == 'nonprofit':
            self._generate_nonprofit_profile(profile, template, analysis)
        else:
            # Fallback to family for unknown types
            self._generate_family_profile(profile, template, analysis)
        
        return profile
    
    def _generate_family_profile(self, profile: Profile, template: ProfileTemplate, analysis: Dict[str, Any]):
        """Generate family household banking profile."""
        # Use profile's unique seed (already set in build_profile)
        random.seed(profile.generation_seed + 1)
        
        # Set household characteristics
        profile.household_type = "family"
        profile.total_members = random.randint(3, 5)
        profile.banking_members = 2  # Two adult banking customers
        
        # Generate realistic income
        if analysis['revenue_range']:
            min_income, max_income = analysis['revenue_range']
        else:
            min_income, max_income = 75000, 120000
        profile.household_income = Decimal(random.randint(min_income, max_income))
        
        # Create family customers with diverse names
        ages = [random.randint(28, 40), random.randint(26, 38)]
        
        # Expanded name pools for variety
        male_names = ["James", "Michael", "David", "John", "Robert", "Christopher", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Daniel", "Brian", "Justin", "Brandon", "Adam"]
        female_names = ["Mary", "Jennifer", "Lisa", "Michelle", "Sarah", "Jessica", "Ashley", "Amanda", "Melissa", "Deborah", "Stephanie", "Dorothy", "Carol", "Ruth", "Sharon", "Helen", "Nancy", "Betty", "Karen", "Susan"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        
        first_names = [
            random.choice(male_names),
            random.choice(female_names)
        ]
        last_name = random.choice(last_names)
        
        employment_options = [
            "Software Engineer", "Nurse", "Teacher", "Financial Analyst", 
            "Marketing Manager", "Project Manager", "Data Analyst"
        ]
        
        for i, (age, first_name) in enumerate(zip(ages, first_names)):
            profile.customers_data.append({
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "employment_status": random.choice(employment_options),
                "role": "primary" if i == 0 else "spouse"
            })
        
        # Create family accounts
        profile.accounts_data.extend([
            {"account_type": AccountType.CHECKING.value, "name": "Joint Checking", "initial_balance": random.randint(2000, 8000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Emergency Fund", "initial_balance": random.randint(10000, 25000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Children's Education", "initial_balance": random.randint(5000, 15000)},
            {"account_type": AccountType.CREDIT.value, "name": "Family Credit Card", "initial_balance": -random.randint(1000, 5000)},
            {"account_type": AccountType.CHECKING.value, "name": "Primary Checking", "initial_balance": random.randint(1500, 4000)},
            {"account_type": AccountType.CREDIT.value, "name": "Secondary Credit Card", "initial_balance": -random.randint(500, 2500)}
        ])
        
        # Add family transaction profile
        tx_profile = TransactionProfile()
        tx_profile.income_sources = [
            {"type": "salary", "amount": float(profile.household_income) * 0.6, "frequency": "biweekly", "description": "Primary earner salary"},
            {"type": "salary", "amount": float(profile.household_income) * 0.4, "frequency": "biweekly", "description": "Secondary earner salary"}
        ]
        tx_profile.spending_categories = {
            "groceries": {"avg_amount": 150, "frequency": "weekly", "variability": "low"},
            "utilities": {"avg_amount": 250, "frequency": "monthly", "variability": "low"},
            "mortgage": {"avg_amount": 1800, "frequency": "monthly", "variability": "none"},
            "childcare": {"avg_amount": 800, "frequency": "monthly", "variability": "low"},
            "dining": {"avg_amount": 80, "frequency": "weekly", "variability": "medium"},
            "gas": {"avg_amount": 60, "frequency": "weekly", "variability": "medium"},
            "shopping": {"avg_amount": 200, "frequency": "weekly", "variability": "high"}
        }
        profile.transaction_profiles["household"] = tx_profile
    
    def _generate_restaurant_profile(self, profile: Profile, template: ProfileTemplate, analysis: Dict[str, Any]):
        """Generate restaurant business banking profile."""
        # Use profile's unique seed (already set in build_profile)  
        random.seed(profile.generation_seed + 2)
        
        profile.household_type = "business"
        profile.total_members = 1  # Business entity
        profile.banking_members = 1
        
        # Restaurant revenue based on size
        size = analysis['size']
        if analysis['revenue_range']:
            min_revenue, max_revenue = analysis['revenue_range']
        elif size == 'small':
            min_revenue, max_revenue = 300000, 800000
        elif size == 'large':
            min_revenue, max_revenue = 1500000, 3000000
        else:  # medium
            min_revenue, max_revenue = 800000, 1500000
            
        profile.household_income = Decimal(random.randint(min_revenue, max_revenue))
        
        # Restaurant business profile with diverse names
        restaurant_names = ["Bella Vista", "Corner Bistro", "Garden Cafe", "Main Street Grill", "Family Kitchen", "Riverside Diner", "City Taphouse", "Maple Leaf Cafe", "Golden Dragon", "Pizza Palace", "The Olive Branch", "Sunset Grill", "Harbor View Restaurant"]
        business_name = random.choice(restaurant_names)
        
        # Diverse owner names reflecting restaurant variety
        owner_first_names = ["Maria", "Tony", "Giuseppe", "Carlos", "Elena", "Ahmed", "Priya", "Jin", "Roberto", "Sofia", "Marco", "Fatima", "Chen", "Isabella", "Diego"]
        owner_last_names = ["Rodriguez", "Martinez", "Romano", "Silva", "Chen", "Patel", "Kim", "Garcia", "Nguyen", "Anderson", "Thompson", "Hassan", "Jackson", "Williams", "Lopez"]
        
        owner_first = random.choice(owner_first_names)
        owner_last = random.choice(owner_last_names)
        
        profile.customers_data.append({
            "first_name": owner_first,
            "last_name": owner_last,
            "company_name": f"{business_name} LLC",
            "employment_status": "Restaurant Owner",
            "business_type": "Restaurant", 
            "industry": "Food Service",
            "employees": random.randint(8, 25),
            "establishment_year": random.randint(2010, 2020)
        })
        
        # Restaurant-specific accounts
        profile.accounts_data.extend([
            {"account_type": AccountType.CHECKING.value, "name": "Operating Account", "initial_balance": random.randint(15000, 40000)},
            {"account_type": AccountType.CHECKING.value, "name": "Payroll Account", "initial_balance": random.randint(20000, 35000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Emergency Reserve", "initial_balance": random.randint(25000, 60000)},
            {"account_type": AccountType.CREDIT.value, "name": "Business Credit Line", "initial_balance": -random.randint(5000, 20000)},
            {"account_type": AccountType.CHECKING.value, "name": "Vendor Payments", "initial_balance": random.randint(10000, 25000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Equipment Fund", "initial_balance": random.randint(15000, 35000)}
        ])
        
        # Add restaurant transaction profile
        tx_profile = TransactionProfile()
        tx_profile.income_sources = [
            {"type": "daily_sales", "amount": float(profile.household_income) / 365, "frequency": "daily", "description": "Restaurant daily sales"}
        ]
        tx_profile.spending_categories = {
            "food_suppliers": {"avg_amount": 800, "frequency": "weekly", "variability": "medium"},
            "payroll": {"avg_amount": 3500, "frequency": "biweekly", "variability": "low"},
            "rent": {"avg_amount": 4500, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 650, "frequency": "monthly", "variability": "low"},
            "equipment": {"avg_amount": 300, "frequency": "monthly", "variability": "high"},
            "insurance": {"avg_amount": 450, "frequency": "monthly", "variability": "none"},
            "marketing": {"avg_amount": 200, "frequency": "monthly", "variability": "medium"}
        }
        profile.transaction_profiles["household"] = tx_profile
    
    def _generate_retail_profile(self, profile: Profile, template: ProfileTemplate, analysis: Dict[str, Any]):
        """Generate retail/supermarket business banking profile."""
        # Use profile's unique seed (already set in build_profile)
        random.seed(profile.generation_seed + 3)
        
        profile.household_type = "business"
        profile.total_members = 1
        profile.banking_members = 1
        
        # Supermarket revenue (typically higher than restaurants)
        size = analysis['size']
        if analysis['revenue_range']:
            min_revenue, max_revenue = analysis['revenue_range']
        elif size == 'small':
            min_revenue, max_revenue = 2000000, 5000000
        elif size == 'large':
            min_revenue, max_revenue = 10000000, 25000000
        else:  # medium
            min_revenue, max_revenue = 5000000, 10000000
            
        profile.household_income = Decimal(random.randint(min_revenue, max_revenue))
        
        # Supermarket business profile with diverse names
        store_names = ["Fresh Market", "Community Grocers", "Valley Supermarket", "Main Street Market", "Corner Store Plus", "Neighborhood Foods", "City Market", "Green Valley Grocers", "Metro Supermarket", "Riverside Foods", "Central Market", "Town Square Grocery"]
        business_name = random.choice(store_names)
        
        # Diverse manager names
        manager_first_names = ["David", "Sarah", "Michael", "Jennifer", "Robert", "Patricia", "Lisa", "Kevin", "Susan", "Richard", "Laura", "James", "Nancy", "Daniel", "Karen", "Paul", "Linda", "Mark", "Helen", "Anthony"]
        manager_last_names = ["Johnson", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez"]
        
        manager_first = random.choice(manager_first_names)
        manager_last = random.choice(manager_last_names)
        
        profile.customers_data.append({
            "first_name": manager_first,
            "last_name": manager_last,
            "company_name": f"{business_name} Inc",
            "employment_status": "Store Manager",
            "business_type": "Supermarket/Grocery",
            "industry": "Retail Grocery", 
            "employees": random.randint(35, 80),
            "establishment_year": random.randint(2005, 2018),
            "square_footage": random.randint(15000, 25000)
        })
        
        # Supermarket-specific accounts
        profile.accounts_data.extend([
            {"account_type": AccountType.CHECKING.value, "name": "Daily Operations", "initial_balance": random.randint(50000, 120000)},
            {"account_type": AccountType.CHECKING.value, "name": "Vendor Payments", "initial_balance": random.randint(80000, 150000)},
            {"account_type": AccountType.CHECKING.value, "name": "Payroll Account", "initial_balance": random.randint(40000, 80000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Equipment Reserve", "initial_balance": random.randint(100000, 200000)},
            {"account_type": AccountType.CREDIT.value, "name": "Business Line of Credit", "initial_balance": -random.randint(25000, 75000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Emergency Fund", "initial_balance": random.randint(150000, 300000)}
        ])
        
        # Add supermarket transaction profile
        tx_profile = TransactionProfile()
        tx_profile.income_sources = [
            {"type": "daily_sales", "amount": float(profile.household_income) / 365, "frequency": "daily", "description": "Supermarket daily sales"}
        ]
        tx_profile.spending_categories = {
            "wholesale_groceries": {"avg_amount": 15000, "frequency": "weekly", "variability": "medium"},
            "payroll": {"avg_amount": 8500, "frequency": "biweekly", "variability": "low"},
            "rent": {"avg_amount": 12000, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 1800, "frequency": "monthly", "variability": "low"},
            "equipment_maintenance": {"avg_amount": 800, "frequency": "monthly", "variability": "medium"},
            "insurance": {"avg_amount": 1200, "frequency": "monthly", "variability": "none"},
            "advertising": {"avg_amount": 600, "frequency": "monthly", "variability": "medium"}
        }
        profile.transaction_profiles["household"] = tx_profile
    
    def _generate_nonprofit_profile(self, profile: Profile, template: ProfileTemplate, analysis: Dict[str, Any]):
        """Generate non-profit organization banking profile."""
        # Use profile's unique seed (already set in build_profile)
        random.seed(profile.generation_seed + 4)
        
        profile.household_type = "organization"
        profile.total_members = 1
        profile.banking_members = 1
        
        # Non-profit budget
        size = analysis['size']
        if analysis['revenue_range']:
            min_budget, max_budget = analysis['revenue_range']
        elif size == 'small':
            min_budget, max_budget = 200000, 750000
        elif size == 'large':
            min_budget, max_budget = 2000000, 8000000
        else:  # medium
            min_budget, max_budget = 750000, 2000000
            
        profile.household_income = Decimal(random.randint(min_budget, max_budget))
        
        # Non-profit organization profile with diverse names
        org_names = ["Community Foundation", "Hope Center", "Education Alliance", "Health Initiative", "Youth Services", "Children's Charity", "Environmental Trust", "Arts Council", "Senior Services", "Food Bank Network", "Housing Coalition", "Literacy Project", "Animal Welfare Society"]
        org_name = random.choice(org_names)
        
        # Diverse executive director names
        director_first_names = ["Patricia", "James", "Linda", "Christopher", "Barbara", "Elizabeth", "William", "Maria", "Charles", "Susan", "Joseph", "Margaret", "Thomas", "Dorothy", "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Helen"]
        director_last_names = ["Anderson", "Taylor", "Thomas", "Jackson", "White", "Lewis", "Walker", "Hall", "Allen", "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson"]
        
        director_first = random.choice(director_first_names)
        director_last = random.choice(director_last_names)
        
        profile.customers_data.append({
            "first_name": director_first,
            "last_name": director_last,
            "company_name": f"{org_name} Foundation",
            "employment_status": "Executive Director",
            "organization_type": "Non-Profit",
            "mission_area": random.choice(["Education", "Health", "Community Development", "Social Services"]),
            "employees": random.randint(25, 75),
            "founded_year": random.randint(1995, 2015),
            "tax_exempt_status": "501(c)(3)"
        })
        
        # Non-profit specific accounts
        profile.accounts_data.extend([
            {"account_type": AccountType.CHECKING.value, "name": "General Operating", "initial_balance": random.randint(30000, 80000)},
            {"account_type": AccountType.CHECKING.value, "name": "Restricted Funds", "initial_balance": random.randint(50000, 150000)},
            {"account_type": AccountType.CHECKING.value, "name": "Payroll Account", "initial_balance": random.randint(25000, 60000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Emergency Reserve", "initial_balance": random.randint(75000, 200000)},
            {"account_type": AccountType.SAVINGS.value, "name": "Program Reserves", "initial_balance": random.randint(40000, 100000)},
            {"account_type": AccountType.INVESTMENT.value, "name": "Endowment Fund", "initial_balance": random.randint(100000, 500000)}
        ])
        
        # Add non-profit transaction profile
        tx_profile = TransactionProfile()
        tx_profile.income_sources = [
            {"type": "grants", "amount": float(profile.household_income) * 0.6, "frequency": "quarterly", "description": "Grant funding"},
            {"type": "donations", "amount": float(profile.household_income) * 0.4, "frequency": "monthly", "description": "Individual donations"}
        ]
        tx_profile.spending_categories = {
            "program_expenses": {"avg_amount": 4000, "frequency": "monthly", "variability": "medium"},
            "payroll": {"avg_amount": 5500, "frequency": "biweekly", "variability": "low"},
            "rent": {"avg_amount": 2800, "frequency": "monthly", "variability": "none"},
            "utilities": {"avg_amount": 400, "frequency": "monthly", "variability": "low"},
            "office_supplies": {"avg_amount": 200, "frequency": "monthly", "variability": "medium"},
            "fundraising": {"avg_amount": 300, "frequency": "monthly", "variability": "medium"},
            "professional_services": {"avg_amount": 800, "frequency": "monthly", "variability": "low"}
        }
        profile.transaction_profiles["household"] = tx_profile


def test_enhanced_profile_builder():
    """Test the enhanced profile builder with different entity types."""
    
    print("🧪 Testing Enhanced ProfileBuilder with Entity-Specific Patterns")
    print("=" * 70)
    
    # Create test templates
    templates = [
        ProfileTemplate(
            name="Suburban Family Test",
            description="Middle-class suburban family with two working parents and 2-3 children earning $95,000 annually.",
            category="household"
        ),
        ProfileTemplate(
            name="Restaurant Test", 
            description="Small family-owned Italian restaurant serving lunch and dinner with $500k annual revenue.",
            category="business"
        ),
        ProfileTemplate(
            name="Supermarket Test",
            description="Local independent supermarket serving the community with $8 million annual revenue.",
            category="business" 
        ),
        ProfileTemplate(
            name="Non-Profit Test",
            description="Large community non-profit organization focused on education with $1.5 million annual budget.",
            category="organization"
        )
    ]
    
    builder = EnhancedProfileBuilder(seed=42)
    
    for template in templates:
        print(f"\n🏢 TESTING: {template.name}")
        print("-" * 50)
        
        # Analyze entity type
        analysis = builder.analyzer.analyze_entity_type(template.description)
        print(f"   Entity Type: {analysis['entity_type']}")
        print(f"   Size: {analysis['size']}")
        print(f"   Revenue Range: {analysis['revenue_range']}")
        
        # Build profile
        profile = builder.build_profile(template, template.name)
        print(f"   Generated Income: ${profile.household_income:,}")
        print(f"   Household Type: {profile.household_type}")
        print(f"   Banking Members: {profile.banking_members}")
        print(f"   Accounts: {len(profile.accounts_data)}")
        
        # Show customer/entity data
        if profile.customers_data:
            customer = profile.customers_data[0]
            if 'business_name' in customer:
                print(f"   Business: {customer['business_name']}")
                print(f"   Industry: {customer['business_type']}")
                print(f"   Employees: {customer.get('employees', 'N/A')}")
            elif 'organization_name' in customer:
                print(f"   Organization: {customer['organization_name']}")
                print(f"   Mission: {customer['mission_area']}")
                print(f"   Staff: {customer.get('employees', 'N/A')}")
            else:
                print(f"   Primary: {customer['first_name']} {customer['last_name']}")
                print(f"   Employment: {customer['employment_status']}")
        
        # Show sample accounts
        print(f"   Sample Accounts:")
        for account in profile.accounts_data[:3]:
            balance_str = f"${account['balance']:,}" if account['balance'] > 0 else f"-${abs(account['balance']):,}"
            print(f"     • {account['name']}: {balance_str}")


if __name__ == "__main__":
    test_enhanced_profile_builder()