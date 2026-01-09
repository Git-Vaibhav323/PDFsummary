#!/usr/bin/env python3
"""
Debug script to test full dashboard generation with web search
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.financial_dashboard import FinancialDashboardGenerator

def test_full_dashboard():
    """Test full dashboard generation with web search"""
    
    print("🔍 Testing Full Dashboard Generation...")
    
    # Initialize dashboard generator
    dashboard_gen = FinancialDashboardGenerator()
    
    # Test with a simple company name and no documents (to force web search)
    print("\n📊 Generating dashboard for 'Apple Inc'...")
    try:
        # Use empty document_ids to force web search only
        dashboard_result = dashboard_gen.generate_dashboard([], "Apple Inc")
        
        print(f"Dashboard generated successfully!")
        print(f"Sections: {list(dashboard_result.get('sections', {}).keys())}")
        
        # Check Latest News
        latest_news = dashboard_result.get('sections', {}).get('latest_news', {})
        print(f"\n📰 Latest News:")
        print(f"  Source: {latest_news.get('source')}")
        print(f"  Source badge: {latest_news.get('source_badge')}")
        print(f"  News count: {len(latest_news.get('news', []))}")
        print(f"  Web search active: {latest_news.get('web_search_active')}")
        
        # Check Competitors
        competitors = dashboard_result.get('sections', {}).get('competitors', {})
        print(f"\n🏢 Competitors:")
        print(f"  Source: {competitors.get('source')}")
        print(f"  Source badge: {competitors.get('source_badge')}")
        print(f"  Competitors count: {len(competitors.get('competitors', []))}")
        print(f"  Web search active: {competitors.get('web_search_active')}")
        
    except Exception as e:
        print(f"Dashboard generation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_dashboard()
