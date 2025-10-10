#!/usr/bin/env python3
"""
Profile Database Integration Utilities

This module provides utilities for storing and retrieving ProfileTemplate and Profile
objects in the SQLite database, integrating with the existing SyFi banking system.
"""

import sqlite3
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.syfi.models import ProfileTemplate, Profile, TransactionProfile

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal and date objects."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif hasattr(obj, 'isoformat'):  # datetime and date objects
            return obj.isoformat()
        return super().default(obj)

class ProfileDatabase:
    """Database utilities for Profile and ProfileTemplate management."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Create tables for profiles if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ProfileTemplate table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                created_date TEXT NOT NULL,
                created_by TEXT,
                category TEXT,
                complexity_level TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used_date TEXT,
                tags TEXT,  -- JSON array
                metadata TEXT  -- JSON object
            )
        ''')
        
        # Profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                profile_id TEXT PRIMARY KEY,
                template_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                created_date TEXT NOT NULL,
                household_type TEXT,
                total_members INTEGER,
                banking_members INTEGER,
                household_income TEXT,  -- Decimal as string
                total_assets TEXT,  -- Decimal as string
                total_liabilities TEXT,  -- Decimal as string
                generation_seed INTEGER,
                is_active BOOLEAN DEFAULT 1,
                last_generated_date TEXT,
                generation_count INTEGER DEFAULT 0,
                customers_data TEXT,  -- JSON
                accounts_data TEXT,  -- JSON
                transaction_profiles TEXT,  -- JSON
                customer_relationships TEXT,  -- JSON
                credit_profile TEXT,  -- JSON
                life_events TEXT,  -- JSON
                generation_parameters TEXT,  -- JSON
                tags TEXT,  -- JSON
                metadata TEXT,  -- JSON
                FOREIGN KEY (template_id) REFERENCES profile_templates (template_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_template(self, template: ProfileTemplate) -> bool:
        """Save a ProfileTemplate to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO profile_templates 
                (template_id, name, description, created_date, created_by, 
                 category, complexity_level, usage_count, last_used_date, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template.template_id,
                template.name,
                template.description,
                template.created_date.isoformat(),
                template.created_by,
                template.category,
                template.complexity_level,
                template.usage_count,
                template.last_used_date.isoformat() if template.last_used_date else None,
                json.dumps(template.tags),
                json.dumps(template.metadata, cls=DecimalEncoder)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def load_template(self, template_id: str) -> Optional[ProfileTemplate]:
        """Load a ProfileTemplate from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM profile_templates WHERE template_id = ?', (template_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Reconstruct ProfileTemplate object
            template = ProfileTemplate(
                template_id=row[0],
                name=row[1],
                description=row[2],
                created_date=datetime.fromisoformat(row[3]),
                created_by=row[4] or "",
                category=row[5] or "",
                complexity_level=row[6] or "medium",
                usage_count=row[7] or 0,
                last_used_date=datetime.fromisoformat(row[8]) if row[8] else None,
                tags=json.loads(row[9]) if row[9] else [],
                metadata=json.loads(row[10]) if row[10] else {}
            )
            
            return template
        except Exception as e:
            print(f"Error loading template: {e}")
            return None
    
    def list_templates(self) -> List[ProfileTemplate]:
        """Get all ProfileTemplates from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM profile_templates ORDER BY created_date DESC')
            rows = cursor.fetchall()
            conn.close()
            
            templates = []
            for row in rows:
                template = ProfileTemplate(
                    template_id=row[0],
                    name=row[1],
                    description=row[2],
                    created_date=datetime.fromisoformat(row[3]),
                    created_by=row[4] or "",
                    category=row[5] or "",
                    complexity_level=row[6] or "medium",
                    usage_count=row[7] or 0,
                    last_used_date=datetime.fromisoformat(row[8]) if row[8] else None,
                    tags=json.loads(row[9]) if row[9] else [],
                    metadata=json.loads(row[10]) if row[10] else {}
                )
                templates.append(template)
            
            return templates
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []
    
    def save_profile(self, profile: Profile) -> bool:
        """Save a Profile to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert transaction profiles to JSON
            tx_profiles_json = {}
            for key, tx_profile in profile.transaction_profiles.items():
                tx_profiles_json[key] = tx_profile.to_dict()
            
            cursor.execute('''
                INSERT OR REPLACE INTO profiles 
                (profile_id, template_id, name, description, created_date, 
                 household_type, total_members, banking_members, household_income,
                 total_assets, total_liabilities, generation_seed, is_active,
                 last_generated_date, generation_count, customers_data, accounts_data,
                 transaction_profiles, customer_relationships, credit_profile, 
                 life_events, generation_parameters, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile.profile_id,
                profile.template_id,
                profile.name,
                profile.description,
                profile.created_date.isoformat(),
                profile.household_type,
                profile.total_members,
                profile.banking_members,
                str(profile.household_income) if profile.household_income else None,
                str(profile.total_assets) if profile.total_assets else None,
                str(profile.total_liabilities) if profile.total_liabilities else None,
                profile.generation_seed,
                profile.is_active,
                profile.last_generated_date.isoformat() if profile.last_generated_date else None,
                profile.generation_count,
                json.dumps(profile.customers_data, cls=DecimalEncoder),
                json.dumps(profile.accounts_data, cls=DecimalEncoder),
                json.dumps(tx_profiles_json, cls=DecimalEncoder),
                json.dumps(profile.customer_relationships, cls=DecimalEncoder),
                json.dumps(profile.credit_profile, cls=DecimalEncoder),
                json.dumps(profile.life_events, cls=DecimalEncoder),
                json.dumps(profile.generation_parameters, cls=DecimalEncoder),
                json.dumps(profile.tags),
                json.dumps(profile.metadata, cls=DecimalEncoder)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, profile_id: str) -> Optional[Profile]:
        """Load a Profile from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM profiles WHERE profile_id = ?', (profile_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Reconstruct Profile object
            profile = Profile(
                profile_id=row[0],
                template_id=row[1],
                name=row[2],
                description=row[3] or "",
                created_date=datetime.fromisoformat(row[4]),
                household_type=row[5] or "individual",
                total_members=row[6] or 1,
                banking_members=row[7] or 1,
                household_income=Decimal(row[8]) if row[8] else None,
                total_assets=Decimal(row[9]) if row[9] else None,
                total_liabilities=Decimal(row[10]) if row[10] else None,
                generation_seed=row[11],
                is_active=bool(row[12]),
                last_generated_date=datetime.fromisoformat(row[13]) if row[13] else None,
                generation_count=row[14] or 0,
                customers_data=json.loads(row[15]) if row[15] else [],
                accounts_data=json.loads(row[16]) if row[16] else [],
                customer_relationships=json.loads(row[18]) if row[18] else {},
                credit_profile=json.loads(row[19]) if row[19] else {},
                life_events=json.loads(row[20]) if row[20] else [],
                generation_parameters=json.loads(row[21]) if row[21] else {},
                tags=json.loads(row[22]) if row[22] else [],
                metadata=json.loads(row[23]) if row[23] else {}
            )
            
            # Reconstruct transaction profiles
            if row[17]:  # transaction_profiles JSON
                tx_profiles_data = json.loads(row[17])
                for key, tx_data in tx_profiles_data.items():
                    tx_profile = TransactionProfile(
                        profile_id=tx_data.get('profile_id', f"TXPF_{key}"),
                        income_sources=tx_data.get('income_sources', []),
                        spending_categories=tx_data.get('spending_categories', {}),
                        transaction_frequency=tx_data.get('transaction_frequency', {}),
                        seasonal_patterns=tx_data.get('seasonal_patterns', {}),
                        preferred_payment_methods=tx_data.get('preferred_payment_methods', []),
                        metadata=tx_data.get('metadata', {})
                    )
                    profile.transaction_profiles[key] = tx_profile
            
            return profile
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def list_profiles(self) -> List[Profile]:
        """Get all Profiles from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT profile_id FROM profiles ORDER BY created_date DESC')
            rows = cursor.fetchall()
            conn.close()
            
            profiles = []
            for row in rows:
                profile = self.load_profile(row[0])
                if profile:
                    profiles.append(profile)
            
            return profiles
        except Exception as e:
            print(f"Error listing profiles: {e}")
            return []

def main():
    """Demonstrate the database integration."""
    
    # Use the existing database structure
    db_path = "data/syfi_bank3.db"
    
    print("Profile Database Integration Demonstration")
    print("=" * 50)
    
    # Initialize database
    profile_db = ProfileDatabase(db_path)
    
    # Create example template and profile
    from examples.profile_example import create_example_profile_template, create_detailed_profile_from_template
    
    template = create_example_profile_template()
    profile = create_detailed_profile_from_template(template)
    
    # Save to database
    print("1. Saving ProfileTemplate to database...")
    success = profile_db.save_template(template)
    print(f"Template saved: {success}")
    
    print("2. Saving Profile to database...")
    success = profile_db.save_profile(profile)
    print(f"Profile saved: {success}")
    
    # Load from database
    print("3. Loading ProfileTemplate from database...")
    loaded_template = profile_db.load_template(template.template_id)
    if loaded_template:
        print(f"Loaded template: {loaded_template.name}")
        print(f"Description: {loaded_template.description[:100]}...")
    
    print("4. Loading Profile from database...")
    loaded_profile = profile_db.load_profile(profile.profile_id)
    if loaded_profile:
        print(f"Loaded profile: {loaded_profile.name}")
        print(f"Banking members: {loaded_profile.banking_members}")
        print(f"Transaction profiles: {len(loaded_profile.transaction_profiles)}")
    
    # List all
    print("5. Listing all templates and profiles...")
    templates = profile_db.list_templates()
    profiles = profile_db.list_profiles()
    
    print(f"Total templates: {len(templates)}")
    print(f"Total profiles: {len(profiles)}")
    
    print("\nDatabase integration successful!")
    print("ProfileTemplate and Profile objects can now be stored and retrieved from SQLite.")

if __name__ == "__main__":
    main()