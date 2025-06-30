#!/usr/bin/env python3
"""Test script to verify the fixes work"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_storm_dataclass_fix():
    """Test that the array fix works"""
    from knowledge_storm.storm_wiki.modules.storm_dataclass import StormInformationTable
    
    # Create empty information table
    empty_table = StormInformationTable([])
    empty_table.prepare_table_for_retrieval()
    
    # This should not crash anymore
    result = empty_table.retrieve_information("test query", 3)
    assert result == [], "Empty table should return empty list"
    print("✅ Array fix working - empty table handled correctly")

def test_perplexity_import():
    """Test that Perplexity RM can be imported"""
    try:
        from knowledge_storm.rm import PerplexityRM
        print("✅ PerplexityRM import successful")
    except Exception as e:
        print(f"❌ PerplexityRM import failed: {e}")

def test_enhanced_outline_import():
    """Test that enhanced outline generation can be imported"""
    try:
        from knowledge_storm.storm_wiki.modules.enhanced_outline_generation import EnhancedStormOutlineGenerationModule
        print("✅ Enhanced outline generation import successful")
    except Exception as e:
        print(f"❌ Enhanced outline import failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing STORM fixes...")
    test_storm_dataclass_fix()
    test_perplexity_import()
    test_enhanced_outline_import()
    print("🎉 All tests completed!")