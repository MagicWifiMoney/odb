#!/usr/bin/env python3
"""
Simple Opportunity Scaling Script
Uses existing Flask app configuration
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.opportunity import db, Opportunity
from src.config.supabase import get_supabase_client
from flask import Flask

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///opportunities.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def generate_synthetic_opportunities(count=10000):
    """Generate synthetic opportunities for scaling"""
    
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
    
    print(f"Generating {count} synthetic opportunities...")
    
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
        
        # Create opportunity object
        opportunity = Opportunity(
            title=title,
            description=description,
            agency_name=agency,
            opportunity_number=f"SYNTH-{random.randint(100000, 999999)}",
            estimated_value=float(estimated_value),
            posted_date=posted_date,
            due_date=due_date,
            source_type=source_type,
            source_name='Synthetic Data Generator',
            location=location,
            contact_info=f"contracting.{agency.lower().replace(' ', '').replace('department', 'dept')}@example.gov",
            keywords=[opp_type.lower(), agency.lower(), location.lower()],
            relevance_score=random.randint(60, 95),
            urgency_score=random.randint(50, 90),
            value_score=random.randint(40, 85),
            competition_score=random.randint(30, 80),
            total_score=random.randint(60, 95)
        )
        
        opportunities.append(opportunity)
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1:,} opportunities...")
    
    return opportunities

def scale_opportunities(target_count=10000):
    """Scale opportunities database to target count"""
    
    app = create_app()
    
    with app.app_context():
        # Get current count
        current_count = db.session.query(Opportunity).count()
        print(f"Current opportunities: {current_count:,}")
        
        if current_count >= target_count:
            print(f"Already at target! Current: {current_count:,}, Target: {target_count:,}")
            return current_count
        
        needed = target_count - current_count
        print(f"Need to add: {needed:,} opportunities")
        
        # Generate opportunities
        opportunities = generate_synthetic_opportunities(needed)
        
        # Bulk insert in batches
        batch_size = 1000
        total_inserted = 0
        
        print(f"Inserting {len(opportunities):,} opportunities in batches of {batch_size}...")
        
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            
            try:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                total_inserted += len(batch)
                
                print(f"Progress: {total_inserted:,}/{len(opportunities):,} opportunities inserted")
                
            except Exception as e:
                print(f"Error inserting batch: {e}")
                db.session.rollback()
                break
        
        # Final count
        final_count = db.session.query(Opportunity).count()
        print(f"🎉 Scaling complete! Final count: {final_count:,} opportunities")
        
        return final_count

if __name__ == "__main__":
    try:
        final_count = scale_opportunities(10000)
        print(f"\n🚀 SUCCESS! Scaled to {final_count:,} opportunities!")
        print(f"🔗 Check your dashboard: https://frontend-ehe4r9mtg-jacobs-projects-cf4c7bdb.vercel.app")
        
    except Exception as e:
        print(f"❌ Scaling failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 