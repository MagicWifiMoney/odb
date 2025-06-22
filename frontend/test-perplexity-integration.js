/**
 * Test script to validate PerplexityPage integration with ContextAwareSearch
 * Run this in the browser console to test the integration
 */

console.log('🧪 Testing PerplexityPage Integration with ContextAwareSearch');

// Test 1: Check if ContextAwareSearch component is properly imported
const checkContextAwareSearchImport = () => {
  const searchComponent = document.querySelector('[data-testid="context-aware-search"]');
  if (searchComponent) {
    console.log('✅ ContextAwareSearch component found in DOM');
    return true;
  } else {
    console.log('❌ ContextAwareSearch component not found in DOM');
    return false;
  }
};

// Test 2: Check if cache statistics are visible
const checkCacheStats = () => {
  const cacheStats = document.querySelector('[data-testid="cache-stats"]');
  if (cacheStats) {
    console.log('✅ Cache statistics component found');
    return true;
  } else {
    console.log('❌ Cache statistics not found');
    return false;
  }
};

// Test 3: Check if smart suggestions are working
const checkSmartSuggestions = () => {
  const suggestions = document.querySelectorAll('[data-testid="smart-suggestion"]');
  if (suggestions.length > 0) {
    console.log(`✅ Found ${suggestions.length} smart suggestions`);
    return true;
  } else {
    console.log('❌ No smart suggestions found');
    return false;
  }
};

// Test 4: Check if query templates are available
const checkQueryTemplates = () => {
  const templates = document.querySelectorAll('[data-testid="query-template"]');
  if (templates.length > 0) {
    console.log(`✅ Found ${templates.length} query templates`);
    return true;
  } else {
    console.log('❌ No query templates found');
    return false;
  }
};

// Run all tests
const runIntegrationTests = () => {
  console.log('🚀 Starting integration tests...');
  
  const results = {
    contextAwareSearch: checkContextAwareSearchImport(),
    cacheStats: checkCacheStats(),
    smartSuggestions: checkSmartSuggestions(),
    queryTemplates: checkQueryTemplates()
  };
  
  const passedTests = Object.values(results).filter(result => result).length;
  const totalTests = Object.keys(results).length;
  
  console.log(`\n📊 Test Results: ${passedTests}/${totalTests} tests passed`);
  
  if (passedTests === totalTests) {
    console.log('🎉 All integration tests passed! PerplexityPage integration is working correctly.');
  } else {
    console.log('⚠️ Some tests failed. Check the console for details.');
  }
  
  return results;
};

// Manual test instructions
console.log(`
📋 Manual Test Instructions:
1. Navigate to the PerplexityPage (/perplexity)
2. Look for the "Smart Suggestions" section at the top
3. Try typing in the custom search input
4. Click on a query template to test template functionality
5. Check the "Cost Optimization" section for cache statistics
6. Run 'runIntegrationTests()' in the console to validate
`);

// Export for browser console use
window.testPerplexityIntegration = runIntegrationTests; 