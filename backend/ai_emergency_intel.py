#!/usr/bin/env python3
"""
AI Emergency Intelligence - On-demand high-priority contract intelligence
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

sys.path.insert(0, os.path.dirname(__file__))

from budget_aware_perplexity import BudgetAwarePerplexity

def run_emergency_intelligence(query_focus: str):
    """Run emergency intelligence query for high-priority opportunities"""
    print("🚨 AI Emergency Intelligence System")
    print("=" * 50)
    print(f"⏰ Query Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Focus Area: {query_focus}")
    
    try:
        # Initialize AI system
        ai = BudgetAwarePerplexity()
        
        # Check budget status first
        budget_status = ai.get_budget_status()
        budget_used = budget_status['budget']['percentage_used']
        remaining = budget_status['budget']['remaining_this_month']
        
        print(f"\n💰 Budget Status:")
        print(f"   Monthly Usage: {budget_used:.1f}%")
        print(f"   Remaining: ${remaining:.2f}")
        
        if budget_used > 95:
            print("❌ CRITICAL: Over 95% budget used. Emergency query may be blocked.")
        elif budget_used > 85:
            print("⚠️ WARNING: Over 85% budget used. Use emergency queries sparingly.")
        else:
            print("✅ Budget healthy for emergency query.")
        
        # Run emergency intelligence
        print(f"\n🔍 Running emergency intelligence query...")
        result = ai.run_emergency_intelligence(query_focus)
        
        if result.get('status') == 'success':
            cost = result.get('cost', 0)
            print(f"\n✅ Emergency Intelligence Complete!")
            print(f"   Cost: ${cost:.3f}")
            print(f"   Query Duration: {result.get('duration', 0):.1f}s")
            
            # Display intelligence summary
            intelligence = result.get('intelligence', {})
            summary = intelligence.get('summary', 'No summary available')
            opportunities = intelligence.get('opportunities_found', 0)
            actionable = len(intelligence.get('actionable_items', []))
            
            print(f"\n📊 Intelligence Summary:")
            print(f"   Opportunities Found: {opportunities}")
            print(f"   Actionable Items: {actionable}")
            print(f"\n📝 Summary:")
            print(f"   {summary}")
            
            if intelligence.get('actionable_items'):
                print(f"\n⚡ Urgent Actions:")
                for item in intelligence['actionable_items'][:3]:  # Show top 3
                    print(f"   • {item}")
                    
        elif result.get('status') == 'blocked':
            reason = result.get('reason', 'Unknown')
            print(f"\n🚫 Emergency query blocked: {reason}")
            
            if 'budget' in reason.lower():
                print(f"   Consider waiting until next month or upgrading budget limit.")
                
        else:
            error = result.get('error', 'Unknown error')
            print(f"\n❌ Emergency query failed: {error}")
        
    except Exception as e:
        print(f"\n💥 Emergency intelligence system error: {e}")

def show_budget_status():
    """Show current AI budget status"""
    print("💰 AI Budget Status Checker")
    print("=" * 40)
    
    try:
        ai = BudgetAwarePerplexity()
        status = ai.get_budget_status()
        
        # Budget overview
        budget = status['budget']
        print(f"Monthly Budget: ${budget['monthly_limit']:.2f}")
        print(f"Emergency Reserve: ${budget['emergency_reserve']:.2f}")
        print(f"Used This Month: ${budget['spent_this_month']:.2f}")
        print(f"Remaining: ${budget['remaining_this_month']:.2f}")
        print(f"Usage: {budget['percentage_used']:.1f}%")
        
        # Daily usage
        daily = status['daily']
        print(f"\nDaily Usage:")
        print(f"Query Limit: {daily['query_limit']}")
        print(f"Queries Used Today: {daily['queries_used']}")
        print(f"Queries Remaining: {daily['queries_remaining']}")
        print(f"Daily Cost: ${daily['estimated_daily_cost']:.3f}")
        
        # Recommendations
        recommendations = status['recommendations']
        print(f"\nRecommendations:")
        print(f"Monthly: {recommendations['monthly']}")
        print(f"Daily: {recommendations['daily']}")
        
    except Exception as e:
        print(f"❌ Error checking budget status: {e}")

def main():
    """Main emergency intelligence interface"""
    if len(sys.argv) < 2:
        print("🚨 AI Emergency Intelligence Tool")
        print("=" * 40)
        print("Usage:")
        print("  python3 ai_emergency_intel.py <query_focus>")
        print("  python3 ai_emergency_intel.py status")
        print("")
        print("Examples:")
        print("  python3 ai_emergency_intel.py 'cybersecurity contracts'")
        print("  python3 ai_emergency_intel.py 'AI and machine learning'")
        print("  python3 ai_emergency_intel.py 'defense contractors'")
        print("  python3 ai_emergency_intel.py status")
        return
    
    command = sys.argv[1]
    
    if command.lower() == 'status':
        show_budget_status()
    else:
        run_emergency_intelligence(command)

if __name__ == "__main__":
    main()