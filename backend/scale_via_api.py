#!/usr/bin/env python3
"""
Scale Opportunities via API
Uses the deployed Railway backend to add opportunities
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Railway API endpoint
API_BASE = "https://web-production-ba1c.up.railway.app"

def generate_opportunity_data(count: int = 1000) -> List[Dict]:
    """Generate synthetic opportunity data"""
    
    agencies = [
        "Department of Defense", "Department of Health and Human Services",
        "Department of Homeland Security", "Department of Veterans Affairs",
        "General Services Administration", "Department of Energy",
        "Department of Transportation", "Department of Education",
        "Environmental Protection Agency", "National Aeronautics and Space Administration",
        "Department of Agriculture", "Department of Commerce",
        "Department of Justice", "Department of Labor",
        "Small Business Administration", "Department of State",
        "Department of Interior", "Department of Treasury",
        "Social Security Administration", "Office of Personnel Management"
    ]
    
    opportunity_types = [
        "IT Services and Solutions", "Construction and Infrastructure",
        "Professional Services", "Research and Development",
        "Medical Equipment and Supplies", "Security Services",
        "Environmental Services", "Training and Education",
        "Logistics and Transportation", "Telecommunications",
        "Energy and Utilities", "Food Services",
        "Maintenance and Repair", "Consulting Services",
        "Software Development", "Cybersecurity Services",
        "Data Analytics", "Cloud Computing Services",
        "Engineering Services", "Financial Services"
    ]
    
    locations = [
        "Washington, DC", "Virginia", "Maryland", "California",
        "Texas", "New York", "Florida", "Illinois",
        "Pennsylvania", "Ohio", "Georgia", "North Carolina",
        "Michigan", "New Jersey", "Arizona", "Tennessee",
        "Colorado", "Massachusetts", "Washington State", "Oregon"
    ]
    
    opportunities = []
    
    print(f"Generating {count} opportunity records...")
    
    for i in range(count):
        # Random opportunity details
        agency = random.choice(agencies)
        opp_type = random.choice(opportunity_types)
        location = random.choice(locations)
        
        # Random dates
        posted_date = datetime.now() - timedelta(days=random.randint(1, 90))
        due_date = posted_date + timedelta(days=random.randint(14, 120))
        
        # Random value with realistic distribution
        value_weights = [0.4, 0.3, 0.2, 0.1]  # Weight towards smaller contracts
        value_ranges = [
            (10000, 100000),      # Small contracts - 40%
            (100000, 1000000),    # Medium contracts - 30%
            (1000000, 10000000),  # Large contracts - 20%
            (10000000, 100000000) # Major contracts - 10%
        ]
        
        selected_range = random.choices(value_ranges, weights=value_weights)[0]
        min_val, max_val = selected_range
        estimated_value = random.randint(min_val, max_val)
        
        # Create realistic titles and descriptions
        title = f"{opp_type} - {agency} - {random.randint(1000, 9999)}"
        
        description_templates = [
            f"Comprehensive {opp_type.lower()} opportunity for {agency}. This contract involves providing high-quality services and solutions to support mission-critical operations.",
            f"The {agency} is seeking qualified contractors to provide {opp_type.lower()} services. This is a multi-year opportunity with potential for extensions.",
            f"Request for proposals for {opp_type.lower()} services to support {agency} operations. Contractors must demonstrate proven experience and capability.",
            f"The {agency} requires {opp_type.lower()} services to enhance operational efficiency and mission effectiveness. This is a competitive procurement."
        ]
        
        description = random.choice(description_templates)
        description += f" Location: {location}. Estimated duration: {random.randint(12, 60)} months."
        
        # Add some variety to source types
        source_types = ['federal_contract', 'federal_grant', 'state_rfp']
        source_weights = [0.7, 0.2, 0.1]
        source_type = random.choices(source_types, weights=source_weights)[0]
        
        opportunity = {
            'external_id': f'scale_{i+1:06d}',
            'title': title,
            'description': description,
            'agency_name': agency,
            'opportunity_number': f'SCALE-{random.randint(100000, 999999)}',
            'estimated_value': float(estimated_value),
            'posted_date': posted_date.isoformat(),
            'due_date': due_date.isoformat(),
            'source_type': source_type,
            'source_name': 'Scaling Script',
            'location': location,
            'contact_info': f'contracting.{agency.lower().replace(" ", "").replace("department", "dept")}@example.gov',
            'keywords': json.dumps([opp_type.lower(), agency.lower(), location.lower()]),
            'relevance_score': random.randint(60, 95),
            'urgency_score': random.randint(50, 90),
            'value_score': random.randint(40, 85),
            'competition_score': random.randint(30, 80),
            'total_score': random.randint(60, 95)
        }
        
        opportunities.append(opportunity)
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1:,} opportunities...")
    
    return opportunities

def check_api_health():
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health: {health_data.get('status', 'unknown')}")
            print(f"📊 Database: {health_data.get('database', 'unknown')}")
            return True
        else:
            print(f"❌ API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check Error: {e}")
        return False

def get_current_count():
    """Get current opportunity count"""
    try:
        response = requests.get(f"{API_BASE}/api/opportunities-simple", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('count', 0)
        else:
            print(f"❌ Failed to get current count: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Error getting current count: {e}")
        return 0

def add_opportunities_batch(opportunities: List[Dict]) -> int:
    """Add a batch of opportunities via API"""
    try:
        # For now, we'll use the init-data endpoint to add sample data
        # In a real implementation, we'd create a bulk insert endpoint
        response = requests.post(f"{API_BASE}/api/init-data", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('added', 0)
        else:
            print(f"❌ Failed to add batch: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Error adding batch: {e}")
        return 0

def scale_opportunities(target_count: int = 10000):
    """Scale opportunities to target count"""
    
    print(f"🚀 Starting opportunity scaling to {target_count:,} opportunities")
    
    # Check API health
    if not check_api_health():
        print("❌ API is not healthy. Cannot proceed.")
        return False
    
    # Get current count
    current_count = get_current_count()
    print(f"📊 Current opportunities: {current_count:,}")
    
    if current_count >= target_count:
        print(f"✅ Already at target! Current: {current_count:,}, Target: {target_count:,}")
        return True
    
    needed = target_count - current_count
    print(f"🎯 Need to add: {needed:,} opportunities")
    
    # Use the new large data endpoint - each call can add up to 1000
    batch_size = 1000
    calls_needed = (needed + batch_size - 1) // batch_size  # Ceiling division
    print(f"📞 Making {calls_needed} API calls to add data in batches of {batch_size}...")
    
    total_added = 0
    for i in range(calls_needed):
        try:
            # Calculate how many to add in this batch
            remaining = needed - total_added
            batch_count = min(batch_size, remaining)
            
            response = requests.post(
                f"{API_BASE}/api/init-data-large", 
                json={'count': batch_count},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                added = data.get('added', 0)
                total_added += added
                
                print(f"Batch {i+1}/{calls_needed}: Added {added} opportunities (Total: {total_added})")
                
                # Check if we've reached the target
                if total_added >= needed:
                    print(f"🎯 Target reached! Added {total_added} opportunities")
                    break
                    
                # Small delay between batches
                time.sleep(0.5)
                
            else:
                print(f"❌ API call {i+1} failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                
        except Exception as e:
            print(f"❌ Error in API call {i+1}: {e}")
            continue
    
    # Final count
    final_count = get_current_count()
    print(f"🎉 Scaling complete! Final count: {final_count:,} opportunities")
    
    return final_count >= target_count

def main():
    """Main execution function"""
    try:
        success = scale_opportunities(5000)  # Scale to 5000 opportunities
        
        if success:
            final_count = get_current_count()
            print(f"\n🚀 SUCCESS! Scaled to {final_count:,} opportunities!")
            print(f"🔗 Check your dashboard: https://frontend-ehe4r9mtg-jacobs-projects-cf4c7bdb.vercel.app")
        else:
            print(f"\n❌ Scaling incomplete. Check the logs above.")
        
    except Exception as e:
        print(f"❌ Scaling failed: {e}")
        return False

if __name__ == "__main__":
    main() 