from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, desc, asc
from src.models.opportunity import db, Opportunity
from src.services.scoring_service import ScoringService
from src.services.data_sync_service import DataSyncService
import logging

opportunities_bp = Blueprint('opportunities', __name__)
logger = logging.getLogger(__name__)


@opportunities_bp.route('/opportunities', methods=['GET'])
def get_opportunities():
    """Get opportunities with filtering, sorting, and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)  # Max 200 per page for large datasets
        
        # Filtering parameters
        source_type = request.args.get('source_type')
        status = request.args.get('status', 'active')
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        min_value = request.args.get('min_value', type=float)
        max_value = request.args.get('max_value', type=float)
        agency = request.args.get('agency')
        state = request.args.get('state')
        keyword = request.args.get('keyword')
        due_within_days = request.args.get('due_within_days', type=int)
        
        # Sorting parameters
        sort_by = request.args.get('sort_by', 'total_score')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = db.session.query(Opportunity)
        
        # Apply filters
        if source_type:
            query = query.filter(Opportunity.source_type == source_type)
        
        # Apply status filter for live data
        if status and status != 'all':
            query = query.filter(Opportunity.status == status)
        
        if min_score is not None:
            query = query.filter(Opportunity.total_score >= min_score)
        
        if max_score is not None:
            query = query.filter(Opportunity.total_score <= max_score)
        
        if min_value is not None:
            query = query.filter(Opportunity.estimated_value >= min_value)
        
        if max_value is not None:
            query = query.filter(Opportunity.estimated_value <= max_value)
        
        if agency:
            query = query.filter(Opportunity.agency_name.ilike(f'%{agency}%'))
        
        if state:
            query = query.filter(Opportunity.location.ilike(f'%{state}%'))
        
        if keyword:
            query = query.filter(
                or_(
                    Opportunity.title.ilike(f'%{keyword}%'),
                    Opportunity.description.ilike(f'%{keyword}%')
                )
            )
        
        if due_within_days:
            cutoff_date = date.today() + timedelta(days=due_within_days)
            query = query.filter(
                and_(
                    Opportunity.due_date.isnot(None),
                    Opportunity.due_date <= cutoff_date,
                    Opportunity.due_date >= date.today()
                )
            )
        
        # Apply sorting
        if hasattr(Opportunity, sort_by):
            sort_column = getattr(Opportunity, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sort by total_score descending
            query = query.order_by(desc(Opportunity.total_score))
        
        # Get total count efficiently
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        opportunities_data = query.offset(offset).limit(per_page).all()
        
        # Convert to dict with selective fields for performance
        opportunities = []
        for opp in opportunities_data:
            opportunities.append({
                'id': opp.id,
                'title': opp.title,
                'agency_name': opp.agency_name,
                'estimated_value': opp.estimated_value,
                'due_date': opp.due_date.isoformat() if opp.due_date else None,
                'posted_date': opp.posted_date.isoformat() if opp.posted_date else None,
                'source_type': opp.source_type,
                'source_name': opp.source_name,
                'total_score': opp.total_score,
                'relevance_score': opp.relevance_score,
                'urgency_score': opp.urgency_score,
                'value_score': opp.value_score,
                'competition_score': opp.competition_score,
                'location': opp.location,
                'opportunity_number': opp.opportunity_number,
                'status': getattr(opp, 'status', 'active')
            })
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            'opportunities': opportunities,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'total': total_count,
            'pages': total_pages
        })
        
    except Exception as e:
        logger.error(f"Error fetching opportunities: {str(e)}")
        return jsonify({'error': 'Failed to fetch opportunities'}), 500


@opportunities_bp.route('/opportunities/<int:opportunity_id>', methods=['GET'])
def get_opportunity(opportunity_id):
    """Get a specific opportunity by ID"""
    try:
        opportunity = db.session.query(Opportunity).get(opportunity_id)
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        return jsonify(opportunity.to_dict())
        
    except Exception as e:
        logger.error(f"Error fetching opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch opportunity'}), 500


@opportunities_bp.route('/opportunities/<int:opportunity_id>/score-explanation', methods=['GET'])
def get_score_explanation(opportunity_id):
    """Get detailed explanation of how an opportunity was scored"""
    try:
        opportunity = db.session.query(Opportunity).get(opportunity_id)
        
        if not opportunity:
            return jsonify({'error': 'Opportunity not found'}), 404
        
        # Get user keywords from query params (if provided)
        user_keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else []
        user_keywords = [k.strip() for k in user_keywords if k.strip()]
        
        scoring_service = ScoringService(user_keywords=user_keywords)
        explanation = scoring_service.get_scoring_explanation(opportunity.to_dict())
        
        return jsonify(explanation)
        
    except Exception as e:
        logger.error(f"Error getting score explanation for opportunity {opportunity_id}: {str(e)}")
        return jsonify({'error': 'Failed to get score explanation'}), 500


@opportunities_bp.route('/opportunities/stats', methods=['GET'])
def get_opportunities_stats():
    """Get statistics about opportunities"""
    try:
        # Basic counts
        total_count = db.session.query(Opportunity).count()
        # Remove active_count since we don't have status field
        # active_count = db.session.query(Opportunity).filter_by(status='active').count()
        
        # Count by source type
        source_type_counts = db.session.query(
            Opportunity.source_type,
            db.func.count(Opportunity.id)
        ).group_by(Opportunity.source_type).all()
        
        # Count by agency (top 10)
        agency_counts = db.session.query(
            Opportunity.agency_name,
            db.func.count(Opportunity.id)
        ).filter(
            Opportunity.agency_name.isnot(None)
        ).group_by(
            Opportunity.agency_name
        ).order_by(
            desc(db.func.count(Opportunity.id))
        ).limit(10).all()
        
        # Count by location (top 10) - using location field instead of state
        location_counts = db.session.query(
            Opportunity.location,
            db.func.count(Opportunity.id)
        ).filter(
            Opportunity.location.isnot(None)
        ).group_by(
            Opportunity.location
        ).order_by(
            desc(db.func.count(Opportunity.id))
        ).limit(10).all()
        
        # Value statistics
        value_stats = db.session.query(
            db.func.avg(Opportunity.estimated_value),
            db.func.min(Opportunity.estimated_value),
            db.func.max(Opportunity.estimated_value),
            db.func.sum(Opportunity.estimated_value)
        ).filter(
            Opportunity.estimated_value.isnot(None)
        ).first()
        
        # Score distribution
        score_ranges = [
            ('90-100', db.session.query(Opportunity).filter(Opportunity.total_score >= 90).count()),
            ('80-89', db.session.query(Opportunity).filter(
                and_(Opportunity.total_score >= 80, Opportunity.total_score < 90)
            ).count()),
            ('70-79', db.session.query(Opportunity).filter(
                and_(Opportunity.total_score >= 70, Opportunity.total_score < 80)
            ).count()),
            ('60-69', db.session.query(Opportunity).filter(
                and_(Opportunity.total_score >= 60, Opportunity.total_score < 70)
            ).count()),
            ('Below 60', db.session.query(Opportunity).filter(Opportunity.total_score < 60).count())
        ]
        
        # Due date distribution
        today = date.today()
        due_soon_counts = [
            ('Overdue', db.session.query(Opportunity).filter(
                and_(Opportunity.due_date.isnot(None), Opportunity.due_date < today)
            ).count()),
            ('Due in 7 days', db.session.query(Opportunity).filter(
                and_(
                    Opportunity.due_date.isnot(None),
                    Opportunity.due_date >= today,
                    Opportunity.due_date <= today + timedelta(days=7)
                )
            ).count()),
            ('Due in 30 days', db.session.query(Opportunity).filter(
                and_(
                    Opportunity.due_date.isnot(None),
                    Opportunity.due_date > today + timedelta(days=7),
                    Opportunity.due_date <= today + timedelta(days=30)
                )
            ).count()),
            ('Due later', db.session.query(Opportunity).filter(
                and_(
                    Opportunity.due_date.isnot(None),
                    Opportunity.due_date > today + timedelta(days=30)
                )
            ).count())
        ]
        
        return jsonify({
            'total_opportunities': total_count,
            'active_opportunities': total_count,  # Use total since we don't have status
            'source_types': dict(source_type_counts),
            'top_agencies': dict(agency_counts),
            'top_locations': dict(location_counts),  # Changed from top_states
            'value_statistics': {
                'average': float(value_stats[0]) if value_stats[0] else 0,
                'minimum': float(value_stats[1]) if value_stats[1] else 0,
                'maximum': float(value_stats[2]) if value_stats[2] else 0,
                'total': float(value_stats[3]) if value_stats[3] else 0
            },
            'score_distribution': dict(score_ranges),
            'due_date_distribution': dict(due_soon_counts)
        })
        
    except Exception as e:
        logger.error(f"Error fetching opportunity stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@opportunities_bp.route('/opportunities/search', methods=['POST'])
def search_opportunities():
    """Advanced search for opportunities"""
    try:
        search_data = request.get_json()
        
        if not search_data:
            return jsonify({'error': 'No search criteria provided'}), 400
        
        # Get search parameters
        keywords = search_data.get('keywords', [])
        agencies = search_data.get('agencies', [])
        states = search_data.get('states', [])
        source_types = search_data.get('source_types', [])
        min_value = search_data.get('min_value')
        max_value = search_data.get('max_value')
        min_score = search_data.get('min_score')
        due_within_days = search_data.get('due_within_days')
        
        # Build query
        query = db.session.query(Opportunity).filter_by(status='active')
        
        # Keyword search
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(
                    or_(
                        Opportunity.title.ilike(f'%{keyword}%'),
                        Opportunity.description.ilike(f'%{keyword}%')
                    )
                )
            query = query.filter(or_(*keyword_conditions))
        
        # Agency filter
        if agencies:
            query = query.filter(Opportunity.agency_name.in_(agencies))
        
        # State filter
        if states:
            query = query.filter(Opportunity.place_of_performance_state.in_(states))
        
        # Source type filter
        if source_types:
            query = query.filter(Opportunity.source_type.in_(source_types))
        
        # Value range filter
        if min_value is not None:
            query = query.filter(Opportunity.estimated_value >= min_value)
        if max_value is not None:
            query = query.filter(Opportunity.estimated_value <= max_value)
        
        # Score filter
        if min_score is not None:
            query = query.filter(Opportunity.total_score >= min_score)
        
        # Due date filter
        if due_within_days:
            cutoff_date = date.today() + timedelta(days=due_within_days)
            query = query.filter(
                and_(
                    Opportunity.due_date.isnot(None),
                    Opportunity.due_date <= cutoff_date,
                    Opportunity.due_date >= date.today()
                )
            )
        
        # Re-score opportunities with user keywords if provided
        opportunities = query.order_by(desc(Opportunity.total_score)).limit(100).all()
        
        if keywords:
            scoring_service = ScoringService(user_keywords=keywords)
            opportunities_data = [opp.to_dict() for opp in opportunities]
            scored_opportunities = scoring_service.score_opportunities(opportunities_data)
        else:
            scored_opportunities = [opp.to_dict() for opp in opportunities]
        
        return jsonify({
            'opportunities': scored_opportunities,
            'total_found': len(scored_opportunities)
        })
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {str(e)}")
        return jsonify({'error': 'Failed to search opportunities'}), 500


@opportunities_bp.route('/sync', methods=['POST'])
def sync_data():
    """Trigger data synchronization from all sources"""
    try:
        sync_service = DataSyncService()
        results = sync_service.sync_all_sources()
        
        return jsonify({
            'message': 'Data synchronization completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error during data sync: {str(e)}")
        return jsonify({'error': 'Failed to synchronize data'}), 500


@opportunities_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """Get status of data synchronization"""
    try:
        sync_service = DataSyncService()
        status = sync_service.get_sync_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error fetching sync status: {str(e)}")
        return jsonify({'error': 'Failed to fetch sync status'}), 500

