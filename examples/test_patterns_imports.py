#!/usr/bin/env python3
"""
Minimal Gang of Four Patterns Test
"""

import os
import sys
from pathlib import Path

# Add src to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_imports():
    """Test each import individually to find issues."""
    
    print("Testing imports...")
    
    # Test 1: DatabaseManager
    try:
        from syfi.database import DatabaseManager
        print("✅ DatabaseManager imported")
    except Exception as e:
        print(f"❌ DatabaseManager failed: {e}")
        return False
    
    # Test 2: Factory Pattern
    try:
        from syfi.patterns.factories import FamilyDataGeneratorFactory
        print("✅ Factory patterns imported")
    except Exception as e:
        print(f"❌ Factory patterns failed: {e}")
        return False
    
    # Test 3: Strategy Pattern
    try:
        from syfi.patterns.strategies import StandardFamilyStrategy
        print("✅ Strategy patterns imported")
    except Exception as e:
        print(f"❌ Strategy patterns failed: {e}")
        return False
        
    # Test 4: All patterns via __init__
    try:
        from syfi.patterns import (
            FamilyDataGeneratorFactory,
            StandardFamilyStrategy
        )
        print("✅ Patterns __init__ imported")
    except Exception as e:
        print(f"❌ Patterns __init__ failed: {e}")
        return False
    
    return True

def main():
    """Run basic test."""
    print("🧪 TESTING GANG OF FOUR PATTERNS IMPORTS")
    print("=" * 50)
    
    if test_imports():
        print("\n🎉 All imports successful!")
        
        # Import for main function use
        from syfi.database import DatabaseManager
        from syfi.patterns.factories import FamilyDataGeneratorFactory
        
        # Quick functionality test
        db_path = "data/test_patterns.db"
        db_manager = DatabaseManager(db_path)
        print(f"✅ DatabaseManager created: {db_path}")
        
        # Test factory
        factory = FamilyDataGeneratorFactory()
        print(f"✅ Factory created: {type(factory).__name__}")
        
        db_manager.close()
        print("✅ Database closed")
        
    else:
        print("\n❌ Import tests failed!")

if __name__ == "__main__":
    main()