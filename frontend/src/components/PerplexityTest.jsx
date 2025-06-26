import React, { useState } from 'react';
import { apiClient } from '../lib/api';

const PerplexityTest = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const checkStatus = async () => {
    try {
      const statusResult = await apiClient.getPerplexityStatus();
      setStatus(statusResult);
    } catch (error) {
      console.error('Error checking Perplexity status:', error);
      setStatus({ error: error.message });
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setResult(null);
    
    try {
      const searchResult = await apiClient.searchFinancialData(query);
      setResult(searchResult);
    } catch (error) {
      console.error('Error searching with Perplexity:', error);
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">
          🧠 Perplexity AI Market Intelligence
        </h2>
        
        {/* Status Check */}
        <div className="mb-6 p-4 rounded-lg bg-gray-50">
          <h3 className="font-semibold mb-2">API Status:</h3>
          {status ? (
            <div className={`p-2 rounded ${status.configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {status.configured ? '✅ Perplexity API Ready' : '❌ API Key Not Configured'}
            </div>
          ) : (
            <div className="p-2 rounded bg-gray-100">Checking...</div>
          )}
        </div>

        {/* Search Interface */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Market Intelligence Query:
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., 'AI defense contracts 2024', 'cybersecurity market trends', 'federal IT spending'"
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim() || !status?.configured}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? '🔄 Analyzing...' : '🔍 Get Market Intelligence'}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div className="mt-6 p-4 rounded-lg bg-gray-50">
            <h3 className="font-semibold mb-3">Analysis Results:</h3>
            {result.error ? (
              <div className="p-3 bg-red-100 text-red-800 rounded">
                Error: {result.error}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="bg-white p-4 rounded border">
                  <div className="text-sm text-gray-600 mb-2">
                    Query: "{result.query}" | Model: {result.model} | {new Date(result.timestamp).toLocaleString()}
                  </div>
                  <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                    {result.analysis}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sample Queries */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold text-blue-800 mb-2">Try these sample queries:</h4>
          <div className="space-y-1">
            {[
              'Defense AI contracts trending upward',
              'Federal cybersecurity spending 2024',
              'Healthcare IT modernization opportunities',
              'Cloud migration government contracts'
            ].map((sample, idx) => (
              <button
                key={idx}
                onClick={() => setQuery(sample)}
                className="block text-left text-blue-600 hover:text-blue-800 text-sm"
              >
                → {sample}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerplexityTest;