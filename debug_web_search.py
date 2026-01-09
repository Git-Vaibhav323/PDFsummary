#!/usr/bin/env python3
"""
Debug script to test web search in Latest News and Competitors sections
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.financial_dashboard import FinancialDashboardGenerator

def test_web_search_sections():
    """Test Latest News and Competitors sections with web search only"""
    
    print("🔍 Testing Web Search Sections...")
    
    # Initialize dashboard generator
    dashboard_gen = FinancialDashboardGenerator()
    
    # Test web search availability
    print(f"Web search available: {dashboard_gen.web_search.is_available()}")
    
    # Test Latest News
    print("\n📰 Testing Latest News...")
    try:
        news_result = dashboard_gen._generate_latest_news("Apple Inc", [])
        print(f"Latest News result keys: {list(news_result.keys())}")
        print(f"News items count: {len(news_result.get('news', []))}")
        print(f"Source: {news_result.get('source')}")
        print(f"Source badge: {news_result.get('source_badge')}")
        if news_result.get('news'):
            print(f"First news item: {news_result['news'][0]}")
    except Exception as e:
        print(f"Latest News error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Competitors
    print("\n🏢 Testing Competitors...")
    try:
        competitors_result = dashboard_gen._generate_competitors("Apple Inc", [])
        print(f"Competitors result keys: {list(competitors_result.keys())}")
        print(f"Competitors count: {len(competitors_result.get('competitors', []))}")
        print(f"Source: {competitors_result.get('source')}")
        print(f"Source badge: {competitors_result.get('source_badge')}")
        if competitors_result.get('competitors'):
            print(f"First competitor: {competitors_result['competitors'][0]}")
    except Exception as e:
        print(f"Competitors error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_search_sections()
