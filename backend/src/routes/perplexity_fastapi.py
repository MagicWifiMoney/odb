import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from ..services.perplexity_client import get_perplexity_client, QueryType
from .perplexity import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/perplexity", tags=["perplexity"])


# Request/Response Models
class PerplexitySearchRequest(BaseModel):
    query: str = Field(..., description="The search query")
    query_type: str = Field(default="search", description="Type of query for optimization")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")
    use_cache: bool = Field(default=True, description="Whether to use caching")
    force_refresh: bool = Field(default=False, description="Force refresh from API")
    similarity_threshold: float = Field(default=0.8, description="Similarity threshold for cached results")


class BatchQueryRequest(BaseModel):
    queries: List[Dict[str, Any]] = Field(..., description="List of queries to batch process")


class QueryStatsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    api_calls: int
    cost_saved: float
    similarity_hits: int
    hit_rate_percent: float
    estimated_savings: str
    cache_efficiency: str
    similarity_efficiency: str


class QueryResponse(BaseModel):
    content: str
    timestamp: str
    query_type: str
    from_cache: bool = False
    from_similar: bool = False
    similarity_score: float = 0.0
    cost_estimate: float = 0.0
    processing_time: float = 0.0
    cache_timestamp: Optional[datetime] = None


class TemplateQueryRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to use")
    params: Dict[str, str] = Field(..., description="Template parameters")


@router.post("/search", response_model=QueryResponse)
async def search_perplexity(
    request: PerplexitySearchRequest,
    current_user: Dict = require_auth
):
    """Enhanced Perplexity search with intelligent caching and optimization"""
    try:
        client = get_perplexity_client()

        # Validate query type
        try:
            query_type = QueryType(request.query_type.lower())
        except ValueError:
            query_type = QueryType.SEARCH

        # Execute optimized query
        result = await client.query(
            query=request.query,
            query_type=query_type,
            params=request.params,
            use_cache=request.use_cache,
            force_refresh=request.force_refresh,
            similarity_threshold=request.similarity_threshold
        )

        # Format response
        response_data = {
            "content": result.data.get('content', ''),
            "timestamp": result.timestamp.isoformat(),
            "query_type": result.query_type.value,
            "from_cache": result.from_cache,
            "from_similar": result.from_similar,
            "similarity_score": result.similarity_score,
            "cost_estimate": result.cost_estimate,
            "processing_time": result.processing_time
        }

        if result.from_cache and hasattr(result, 'cache_timestamp'):
            response_data["cache_timestamp"] = result.data.get('timestamp')

        return QueryResponse(**response_data)

    except Exception as e:
        logger.error(f"Perplexity search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/batch", response_model=List[QueryResponse])
async def batch_query_perplexity(
    request: BatchQueryRequest,
    current_user: Dict = require_auth
):
    """Execute multiple Perplexity queries efficiently using intelligent batching"""
    try:
        client = get_perplexity_client()

        # Execute batch query
        results = await client.batch_query(request.queries)

        # Format responses
        responses = []
        for result in results:
            response_data = {
                "content": result.data.get('content', ''),
                "timestamp": result.timestamp.isoformat(),
                "query_type": result.query_type.value,
                "from_cache": result.from_cache,
                "from_similar": result.from_similar,
                "similarity_score": result.similarity_score,
                "cost_estimate": result.cost_estimate,
                "processing_time": result.processing_time
            }

            if result.from_cache and hasattr(result, 'cache_timestamp'):
                response_data["cache_timestamp"] = result.data.get('timestamp')

            responses.append(QueryResponse(**response_data))

        return responses

    except Exception as e:
        logger.error(f"Batch query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}")


@router.post("/template-query", response_model=QueryResponse)
async def template_query_perplexity(
    request: TemplateQueryRequest,
    current_user: Dict = require_auth
):
    """Execute a templated query for consistent, optimized results"""
    try:
        from ..lib.perplexity_templates import QUERY_TEMPLATES, buildQuery

        # Get template
        template = QUERY_TEMPLATES.get(request.template_id.upper())
        if not template:
            raise HTTPException(status_code=400, detail=f"Template '{request.template_id}' not found")

        # Build query from template
        built_query = buildQuery(request.template_id.upper(), request.params)
        if not built_query['isComplete']:
            missing_params = built_query['remainingPlaceholders']
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters: {missing_params}"
            )

        # Execute query
        client = get_perplexity_client()
        query_type = QueryType(template['category'].lower().replace(' ', '_'))

        result = await client.query(
            query=built_query['query'],
            query_type=query_type,
            params=request.params,
            use_cache=True
        )

        # Format response
        response_data = {
            "content": result.data.get('content', ''),
            "timestamp": result.timestamp.isoformat(),
            "query_type": result.query_type.value,
            "from_cache": result.from_cache,
            "from_similar": result.from_similar,
            "similarity_score": result.similarity_score,
            "cost_estimate": result.cost_estimate,
            "processing_time": result.processing_time
        }

        return QueryResponse(**response_data)

    except Exception as e:
        logger.error(f"Template query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template query failed: {str(e)}")


@router.get("/templates")
async def get_query_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: Dict = require_auth
):
    """Get available query templates for the frontend"""
    try:
        from ..lib.perplexity_templates import QUERY_TEMPLATES, CATEGORIES

        templates = QUERY_TEMPLATES

        if category:
            templates = {
                k: v for k, v in templates.items()
                if v['category'].lower() == category.lower()
            }

        return {
            "templates": templates,
            "categories": CATEGORIES
        }

    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.get("/presets")
async def get_query_presets(current_user: Dict = require_auth):
    """Get preset query workflows"""
    try:
        from ..lib.perplexity_templates import PRESET_QUERIES, USAGE_RECOMMENDATIONS

        return {
            "presets": PRESET_QUERIES,
            "usage_recommendations": USAGE_RECOMMENDATIONS
        }

    except Exception as e:
        logger.error(f"Failed to get presets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get presets: {str(e)}")


@router.get("/stats", response_model=QueryStatsResponse)
async def get_perplexity_stats(current_user: Dict = require_auth):
    """Get Perplexity client performance statistics"""
    try:
        client = get_perplexity_client()
        stats = client.get_stats()

        return QueryStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/clear-cache")
async def clear_perplexity_cache(
    query_type: Optional[str] = Query(None, description="Specific query type to clear"),
    current_user: Dict = require_auth
):
    """Clear Perplexity cache (admin only)"""
    try:
        # Check if user has admin privileges
        if not current_user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Admin privileges required")

        client = get_perplexity_client()

        cache_query_type = None
        if query_type:
            try:
                cache_query_type = QueryType(query_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid query type: {query_type}")

        await client.clear_cache(cache_query_type)

        return {
            "message": f"Cache cleared successfully" + (f" for {query_type}" if query_type else ""),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/cache-metadata")
async def get_cache_metadata(current_user: Dict = require_auth):
    """Get cache metadata for debugging and optimization"""
    try:
        client = get_perplexity_client()
        metadata = client.getCacheMetadata()

        return {
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get cache metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache metadata: {str(e)}")


# Legacy endpoints for backward compatibility
@router.post("/query")
async def legacy_query_perplexity(
    query: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = require_auth
):
    """Legacy endpoint for backward compatibility"""
    try:
        request = PerplexitySearchRequest(query=query)
        result = await search_perplexity(request, current_user)
        return result

    except Exception as e:
        logger.error(f"Legacy query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/health")
async def perplexity_health_check():
    """Health check endpoint for Perplexity service"""
    try:
        client = get_perplexity_client()
        stats = client.get_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
\n__all__ = ['router']
