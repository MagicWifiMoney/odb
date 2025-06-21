#!/usr/bin/env python3
"""
Quick Scale Script - Add unique opportunities directly
"""

import requests
import json
import random
import time
from datetime import datetime, timedelta

API_BASE = "https://web-production-ba1c.up.railway.app"

def generate_unique_opportunities(count=100, start_id=1000):
    """Generate unique opportunities"""
    
    agencies = [
        "Department of Defense", "Department of Health and Human Services",
        "Department of Homeland Security", "Department of Veterans Affairs", 
        "General Services Administration", "Department of Energy",
        "Department of Transportation", "Department of Education",
        "Environmental Protection Agency", "NASA",
        "Department of Agriculture", "Department of Commerce",
        "Department of Justice", "Department of Labor",
        "Small Business Administration", "Department of State",
        "Department of Interior", "Department of Treasury",
        "Social Security Administration", "Office of Personnel Management",
        "Department of Housing and Urban Development", "Federal Emergency Management Agency",
        "Centers for Disease Control", "National Institutes of Health",
        "Federal Bureau of Investigation", "Central Intelligence Agency"
    ]
    
    opportunity_types = [
        "IT Infrastructure Modernization", "Cloud Migration Services",
        "Cybersecurity Implementation", "Data Analytics Platform",
        "Software Development", "Network Security", "Database Management",
        "System Integration", "Technical Support Services", "Training Programs",
        "Research and Development", "Consulting Services", "Project Management",
        "Quality Assurance", "Business Intelligence", "Mobile App Development",
        "Web Development", "AI/ML Implementation", "Blockchain Solutions",
        "IoT Infrastructure", "Digital Transformation", "Legacy System Upgrade"
    ]
    
    locations = [
        "Washington, DC", "Arlington, VA", "Bethesda, MD", "Alexandria, VA",
        "San Francisco, CA", "Los Angeles, CA", "San Diego, CA", "Sacramento, CA",
        "Austin, TX", "Dallas, TX", "Houston, TX", "San Antonio, TX",
        "New York, NY", "Albany, NY", "Buffalo, NY", "Rochester, NY",
        "Miami, FL", "Tampa, FL", "Orlando, FL", "Jacksonville, FL",
        "Chicago, IL", "Springfield, IL", "Rockford, IL", "Peoria, IL",
        "Philadelphia, PA", "Pittsburgh, PA", "Harrisburg, PA", "Allentown, PA",
        "Columbus, OH", "Cleveland, OH", "Cincinnati, OH", "Toledo, OH",
        "Atlanta, GA", "Savannah, GA", "Augusta, GA", "Macon, GA",
        "Charlotte, NC", "Raleigh, NC", "Greensboro, NC", "Asheville, NC"
    ]
    
    opportunities = []
    
    for i in range(count):
        unique_id = start_id + i
        agency = random.choice(agencies)
        opp_type = random.choice(opportunity_types)
        location = random.choice(locations)
        
        # Random dates
        posted_date = datetime.now() - timedelta(days=random.randint(1, 180))
        due_date = posted_date + timedelta(days=random.randint(21, 180))
        
        # Random value with realistic distribution
        value_tiers = [
            (25000, 250000, 0.3),      # Small contracts - 30%
            (250000, 2500000, 0.4),    # Medium contracts - 40%
            (2500000, 25000000, 0.2), # Large contracts - 20%
            (25000000, 250000000, 0.1) # Major contracts - 10%
        ]
        
        # Select tier based on weights
        rand_val = random.random()
        cumulative = 0
        for min_val, max_val, weight in value_tiers:
            cumulative += weight
            if rand_val <= cumulative:
                estimated_value = random.randint(min_val, max_val)
                break
        
        # Create unique, detailed opportunity
        title = f"{opp_type} - {agency} - Contract #{unique_id:06d}"
        
        descriptions = [
            f"The {agency} seeks qualified contractors for comprehensive {opp_type.lower()} services. This multi-phase initiative will modernize critical infrastructure and enhance operational capabilities.",
            f"Opportunity for {opp_type.lower()} implementation at {agency}. The selected contractor will provide end-to-end solutions including design, development, testing, and deployment.",
            f"The {agency} requires {opp_type.lower()} services to support mission-critical operations. This contract includes maintenance, support, and potential system expansions.",
            f"Request for {opp_type.lower()} services to enhance {agency} capabilities. The scope includes analysis, implementation, training, and ongoing technical support.",
            f"Major {opp_type.lower()} initiative for {agency}. This opportunity involves cutting-edge technology implementation with significant impact on operational efficiency."
        ]
        
        description = random.choice(descriptions)
        description += f" Primary location: {location}. Contract duration: {random.randint(12, 60)} months. "
        description += f"Security clearance may be required. Small business participation encouraged."
        
        opportunity = {
            'title': title,
            'description': description,
            'agency_name': agency,
            'opportunity_number': f'RFP-{unique_id:06d}-{random.randint(10, 99)}',
            'estimated_value': float(estimated_value),
            'posted_date': posted_date.isoformat(),
            'due_date': due_date.isoformat(),
            'source_type': random.choice(['federal_contract', 'federal_grant', 'state_rfp']),
            'source_name': 'Quick Scale Generator',
            'location': location,
            'contact_info': f'contracting.{unique_id}@{agency.lower().replace(" ", "").replace("department", "dept")}.gov',
            'keywords': json.dumps([opp_type.lower(), agency.lower(), location.lower()]),
            'relevance_score': random.randint(65, 98),
            'urgency_score': random.randint(55, 95),
            'value_score': random.randint(45, 90),
            'competition_score': random.randint(35, 85),
            'total_score': random.randint(60, 95)
        }
        
        opportunities.append(opportunity)
    
    return opportunities

def add_opportunities_via_bulk(opportunities):
    """Add opportunities via bulk endpoint"""
    try:
        response = requests.post(
            f"{API_BASE}/api/bulk-insert",
            json={'opportunities': opportunities},
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('added', 0)
        else:
            print(f"❌ Bulk insert failed: {response.status_code}")
            print(f"Response: {response.text}")
            return 0
            
    except Exception as e:
        print(f"❌ Error in bulk insert: {e}")
        return 0

def get_current_count():
    """Get current opportunity count"""
    try:
        response = requests.get(f"{API_BASE}/api/opportunities-simple", timeout=10)
        if response.status_code == 200:
            return response.json().get('count', 0)
        return 0
    except:
        return 0

def main():
    """Main scaling function"""
    print("🚀 Quick Scale: Adding 5,000 unique opportunities!")
    
    # Get starting count
    start_count = get_current_count()
    print(f"📊 Starting count: {start_count:,} opportunities")
    
    target_additions = 5000
    batch_size = 500  # Smaller batches for reliability
    
    total_added = 0
    start_id = 10000  # Start with high ID to ensure uniqueness
    
    batches = (target_additions + batch_size - 1) // batch_size
    print(f"📦 Processing {batches} batches of {batch_size} opportunities each...")
    
    for batch_num in range(batches):
        print(f"\n🔄 Batch {batch_num + 1}/{batches}")
        
        # Generate batch
        batch_start_id = start_id + (batch_num * batch_size)
        current_batch_size = min(batch_size, target_additions - total_added)
        
        print(f"   Generating {current_batch_size} opportunities (ID range: {batch_start_id}-{batch_start_id + current_batch_size - 1})")
        opportunities = generate_unique_opportunities(current_batch_size, batch_start_id)
        
        # Add via bulk endpoint
        print(f"   Inserting batch via API...")
        added = add_opportunities_via_bulk(opportunities)
        total_added += added
        
        print(f"   ✅ Added {added} opportunities (Total: {total_added:,})")
        
        # Progress check
        if total_added >= target_additions:
            break
            
        # Small delay between batches
        time.sleep(1)
    
    # Final count
    final_count = get_current_count()
    net_added = final_count - start_count
    
    print(f"\n🎉 SCALING COMPLETE!")
    print(f"📊 Final count: {final_count:,} opportunities")
    print(f"✅ Net added: {net_added:,} opportunities")
    print(f"🎯 Target met: {net_added >= target_additions}")
    print(f"🔗 View dashboard: https://frontend-ehe4r9mtg-jacobs-projects-cf4c7bdb.vercel.app")

if __name__ == "__main__":
    main() 