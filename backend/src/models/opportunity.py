from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index

db = SQLAlchemy()

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    agency_name = db.Column(db.String(200))
    opportunity_number = db.Column(db.String(100))
    estimated_value = db.Column(db.Float)
    posted_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    source_type = db.Column(db.String(50), nullable=False)
    source_name = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(500))
    location = db.Column(db.String(200))
    contact_info = db.Column(db.Text)
    keywords = db.Column(db.JSON)
    
    # Scoring fields
    relevance_score = db.Column(db.Integer, default=0)
    urgency_score = db.Column(db.Integer, default=0)
    value_score = db.Column(db.Integer, default=0)
    competition_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    
    # Metadata
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert opportunity to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'agency_name': self.agency_name,
            'opportunity_number': self.opportunity_number,
            'estimated_value': float(self.estimated_value) if self.estimated_value else None,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'source_type': self.source_type,
            'source_name': self.source_name,
            'source_url': self.source_url,
            'location': self.location,
            'contact_info': self.contact_info,
            'keywords': self.keywords or [],
            'relevance_score': self.relevance_score or 0,
            'urgency_score': self.urgency_score or 0,
            'value_score': self.value_score or 0,
            'competition_score': self.competition_score or 0,
            'total_score': self.total_score or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DataSource(db.Model):
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    source_type = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(100), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False, default='api')
    sync_start = db.Column(db.DateTime, nullable=False)
    sync_end = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='running')
    records_processed = db.Column(db.Integer, default=0)
    records_added = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    errors_count = db.Column(db.Integer, default=0)


# Create indexes for better performance
Index('idx_opportunities_due_date', Opportunity.due_date)
Index('idx_opportunities_posted_date', Opportunity.posted_date)
Index('idx_opportunities_source_type', Opportunity.source_type)
Index('idx_opportunities_total_score', Opportunity.total_score.desc())
Index('idx_opportunities_estimated_value', Opportunity.estimated_value.desc())
Index('idx_opportunities_agency', Opportunity.agency_name)

