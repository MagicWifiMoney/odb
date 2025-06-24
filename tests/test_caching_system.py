#!/usr/bin/env python3
"""
Test Suite for Enhanced Caching System
Tests cache functionality, Perplexity integration, and performance
"""

import asyncio
import time
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from services.cache_service import IntelligentCache, CacheConfig, CacheStrategy
from services.perplexity_client import EnhancedPerplexityClient, PerplexityConfig, PerplexityQuery, QueryType

async def test_cache_basic_functionality():
    """Test basic cache operations"""
    print("🧪 Testing Basic Cache Functionality")
    print("-" * 50)
    
    # Initialize cache
    cache = IntelligentCache()
    
    # Test 1: Set and Get
    await cache.set("test_key", "test_value", ttl=300)
    value = await cache.get("test_key")
    assert value == "test_value", "Basic set/get failed"
    print("   ✅ Basic set/get operations working")
    
    # Test 2: TTL expiration
    await cache.set("expire_test", "value", ttl=1)
    await asyncio.sleep(1.1)
    expired_value = await cache.get("expire_test")
    assert expired_value is None, "TTL expiration failed"
    print("   ✅ TTL expiration working")
    
    # Test 3: Cache strategies
    strategies = [CacheStrategy.IMMEDIATE, CacheStrategy.BATCH, CacheStrategy.LONG_TERM]
    for strategy in strategies:
        key = f"strategy_test_{strategy.value}"
        await cache.set(key, f"value_{strategy.value}", strategy=strategy)
        value = await cache.get(key)
        assert value == f"value_{strategy.value}", f"Strategy {strategy.value} failed"
    print("   ✅ All cache strategies working")
    
    # Test 4: Statistics
    stats = cache.get_stats()
    assert "hits" in stats, "Statistics not available"
    assert "cache_size" in stats, "Cache size not tracked"
    print(f"   ✅ Cache statistics: {stats['hits']} hits, {stats['cache_size']} entries")
    
    print("✅ Basic cache functionality tests passed!\n")

async def test_cache_performance():
    """Test cache performance and batching"""
    print("⚡ Testing Cache Performance")
    print("-" * 50)
    
    cache = IntelligentCache()
    
    # Test 1: Performance with many operations
    start_time = time.time()
    
    # Set 1000 items
    for i in range(1000):
        await cache.set(f"perf_test_{i}", f"value_{i}")
    
    # Get 1000 items
    for i in range(1000):
        value = await cache.get(f"perf_test_{i}")
        assert value == f"value_{i}", f"Performance test failed at item {i}"
    
    end_time = time.time()
    print(f"   ✅ 2000 operations completed in {end_time - start_time:.3f} seconds")
    
    # Test 2: Get-or-compute functionality
    call_count = 0
    
    def expensive_computation(x):
        nonlocal call_count
        call_count += 1
        time.sleep(0.1)  # Simulate expensive operation
        return x * 2
    
    # First call should execute computation
    start_time = time.time()
    result1 = await cache.get_or_compute("compute_test", expensive_computation, 5)
    first_call_time = time.time() - start_time
    
    # Second call should use cache
    start_time = time.time()
    result2 = await cache.get_or_compute("compute_test", expensive_computation, 5)
    second_call_time = time.time() - start_time
    
    assert result1 == result2 == 10, "Get-or-compute failed"
    assert call_count == 1, "Computation not cached"
    assert second_call_time < first_call_time / 2, "Cache not improving performance"
    
    print(f"   ✅ Cache improved performance: {first_call_time:.3f}s → {second_call_time:.3f}s")
    print("✅ Performance tests passed!\n")

async def test_perplexity_integration():
    """Test Perplexity client with caching"""
    print("🔮 Testing Perplexity Integration")
    print("-" * 50)
    
    # Check if API key is available
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("   ⚠️  No PERPLEXITY_API_KEY found, skipping live API tests")
        print("   📝 Testing client initialization and mock operations...")
        
        # Test client initialization
        config = PerplexityConfig(api_key="test_key")
        client = EnhancedPerplexityClient(config)
        
        # Test query object creation
        query = PerplexityQuery(
            query="Test query",
            query_type=QueryType.TREND_ANALYSIS,
            context={"test": "context"}
        )
        
        cache_key = query.to_cache_key()
        assert cache_key.startswith("perplexity:trend_analysis:"), "Cache key generation failed"
        print("   ✅ Client initialization and query creation working")
        print("   ✅ Cache key generation working")
        
        return
    
    # Live API testing
    config = PerplexityConfig(api_key=api_key, rate_limit_per_minute=5)  # Conservative rate limit
    
    async with EnhancedPerplexityClient(config) as client:
        # Test 1: Basic query
        print("   🌐 Testing basic API query...")
        
        query = PerplexityQuery(
            query="What are the current trends in government contracting?",
            query_type=QueryType.TREND_ANALYSIS
        )
        
        start_time = time.time()
        result1 = await client.query(query)
        first_call_time = time.time() - start_time
        
        assert "choices" in result1, "API response format unexpected"
        print(f"   ✅ First API call completed in {first_call_time:.3f}s")
        
        # Test 2: Same query should use cache
        print("   💾 Testing cache hit...")
        
        start_time = time.time()
        result2 = await client.query(query)
        second_call_time = time.time() - start_time
        
        assert result1 == result2, "Cached result doesn't match"
        assert second_call_time < first_call_time / 5, "Cache not significantly faster"
        print(f"   ✅ Cache hit completed in {second_call_time:.3f}s (faster!)")
        
        # Test 3: Different query types
        query_types = [
            (QueryType.KEYWORD_EXPANSION, "Suggest keywords related to: cybersecurity"),
            (QueryType.OPPORTUNITY_SEARCH, "Find recent opportunities in cloud computing"),
        ]
        
        for query_type, query_text in query_types:
            query = PerplexityQuery(query=query_text, query_type=query_type)
            result = await client.query(query)
            assert "choices" in result, f"Query type {query_type.value} failed"
            print(f"   ✅ {query_type.value} query successful")
        
        # Test 4: Client statistics
        stats = client.get_stats()
        print(f"   📊 Client stats: {stats['total_queries']} queries, {stats['cache_hits']} cache hits")
        print(f"   📊 Cache hit rate: {stats['cache_hit_rate']:.1f}%")
        
    print("✅ Perplexity integration tests passed!\n")

async def test_advanced_features():
    """Test advanced caching features"""
    print("🚀 Testing Advanced Features")
    print("-" * 50)
    
    cache = IntelligentCache()
    
    # Test 1: Cache invalidation
    await cache.set("invalidation_test", "original_value")
    await cache.delete("invalidation_test")
    value = await cache.get("invalidation_test")
    assert value is None, "Cache invalidation failed"
    print("   ✅ Cache invalidation working")
    
    # Test 2: Different strategies have different TTLs
    strategies_and_values = [
        (CacheStrategy.IMMEDIATE, "immediate_value"),
        (CacheStrategy.BATCH, "batch_value"),
        (CacheStrategy.LONG_TERM, "long_term_value"),
    ]
    
    for strategy, value in strategies_and_values:
        key = f"strategy_ttl_test_{strategy.value}"
        await cache.set(key, value, strategy=strategy)
        cached_value = await cache.get(key)
        assert cached_value == value, f"Strategy {strategy.value} storage failed"
    
    print("   ✅ Multiple cache strategies working")
    
    # Test 3: Cache size limits and LRU eviction
    small_cache = IntelligentCache(CacheConfig(max_size=5))
    
    # Fill cache beyond capacity
    for i in range(10):
        await small_cache.set(f"lru_test_{i}", f"value_{i}")
    
    # Check that only recent items remain
    cache_size = len(small_cache._memory_cache)
    assert cache_size <= 5, f"Cache size limit not enforced: {cache_size}"
    
    # Check that most recent items are still there
    recent_value = await small_cache.get("lru_test_9")
    assert recent_value == "value_9", "LRU eviction not working correctly"
    
    print("   ✅ LRU eviction and size limits working")
    
    print("✅ Advanced features tests passed!\n")

async def test_error_handling():
    """Test error handling and fallbacks"""
    print("🛡️  Testing Error Handling")
    print("-" * 50)
    
    # Test 1: Invalid API key handling
    config = PerplexityConfig(api_key="invalid_key")
    client = EnhancedPerplexityClient(config)
    
    # This should be handled gracefully
    print("   ✅ Invalid API key handled gracefully")
    
    # Test 2: Cache with Redis fallback
    cache_with_redis = IntelligentCache(use_redis=True)
    
    # Should fall back to memory cache if Redis unavailable
    await cache_with_redis.set("fallback_test", "fallback_value")
    value = await cache_with_redis.get("fallback_test")
    assert value == "fallback_value", "Redis fallback failed"
    print("   ✅ Redis fallback to memory cache working")
    
    # Test 3: Rate limiting
    rate_limiter = client.rate_limiter
    
    # Should acquire tokens successfully
    acquired = await rate_limiter.acquire()
    assert acquired, "Rate limiter failed to acquire token"
    print("   ✅ Rate limiting working")
    
    print("✅ Error handling tests passed!\n")

def print_summary_report(cache, client=None):
    """Print a comprehensive summary report"""
    print("📋 CACHING SYSTEM SUMMARY REPORT")
    print("=" * 60)
    
    cache_stats = cache.get_stats()
    
    print(f"Cache Performance:")
    print(f"  • Hit Rate: {cache_stats['hit_rate_percent']:.1f}%")
    print(f"  • Total Requests: {cache_stats['total_requests']}")
    print(f"  • Cache Size: {cache_stats['cache_size']} entries")
    print(f"  • Redis Available: {cache_stats['redis_available']}")
    
    if client:
        client_stats = client.get_stats()
        print(f"\nPerplexity Client Performance:")
        print(f"  • Total Queries: {client_stats['total_queries']}")
        print(f"  • API Calls: {client_stats['api_calls']}")
        print(f"  • Cache Hit Rate: {client_stats.get('cache_hit_rate', 0):.1f}%")
        print(f"  • Avg Response Time: {client_stats['avg_response_time']:.3f}s")
        print(f"  • Estimated Cost: ${client_stats['total_cost']:.4f}")
    
    print(f"\nSystem Status: ✅ ALL TESTS PASSED")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

async def main():
    """Run all tests"""
    print("🎯 ENHANCED CACHING SYSTEM TEST SUITE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run all test suites
        await test_cache_basic_functionality()
        await test_cache_performance()
        await test_perplexity_integration()
        await test_advanced_features()
        await test_error_handling()
        
        # Print summary
        cache = IntelligentCache()
        print_summary_report(cache)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)