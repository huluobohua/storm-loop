#!/usr/bin/env python3
"""
Quick test of PerplexityRM to debug the API issue
"""

import os
import pytest

pytest.importorskip("dspy")
from knowledge_storm.rm import PerplexityRM

def test_perplexity_api():
    """Test actual Perplexity API call"""
    print("Testing Perplexity API...")
    
    # Create PerplexityRM instance
    prm = PerplexityRM(
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
        k=1,  # Just one result for testing
        model="sonar-pro"
    )
    
    try:
        # Test with a simple query
        query = "artificial intelligence"
        print(f"Searching for: {query}")
        
        results = prm.forward(query)
        
        print(f"✅ Success! Got {len(results)} results")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'N/A')[:100]}...")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Description: {result.get('description', 'N/A')[:200]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("❌ PERPLEXITY_API_KEY not found in environment")
        exit(1)
    
    test_perplexity_api()
