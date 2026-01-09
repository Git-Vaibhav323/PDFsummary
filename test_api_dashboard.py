#!/usr/bin/env python3
"""
Test API endpoint for dashboard generation
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.routes import FinancialDashboardRequest

async def test_api():
    try:
        # Import the function directly
        from app.api.routes import generate_financial_dashboard
        
        request = FinancialDashboardRequest(document_ids=["dummy-doc-id"], company_name='Apple Inc')
        response = await generate_financial_dashboard(request)
        
        # Extract JSON content from JSONResponse
        import json
        if hasattr(response, 'body'):
            result = json.loads(response.body.decode())
        else:
            result = response
        
        print('✅ API Test Result:')
        latest_news = result.get("sections", {}).get("latest_news", {})
        competitors = result.get("sections", {}).get("competitors", {})
        
        print(f'Latest News source: {latest_news.get("source")}')
        print(f'Latest News badge: {latest_news.get("source_badge")}')
        print(f'Latest News count: {len(latest_news.get("news", []))}')
        print(f'Competitors source: {competitors.get("source")}')
        print(f'Competitors badge: {competitors.get("source_badge")}')
        print(f'Competitors count: {len(competitors.get("competitors", []))}')
        
        # Check if web search is working
        if latest_news.get("source") == "web_search" and competitors.get("source") == "web_search":
            print('\n✅ WEB SEARCH IS WORKING CORRECTLY!')
        else:
            print('\n❌ Web search not working as expected')
            
    except Exception as e:
        print(f'❌ API Test Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
