// API Configuration with Railway backend support
const API_BASE_URL = import.meta.env.VITE_API_URL || 
                     (import.meta.env.PROD ? 'https://odb-production.up.railway.app' : 'http://localhost:5001')

// Log API configuration on startup
console.log('Using API URL:', API_BASE_URL)

// API client class
class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    // Create abort controller with shorter timeout for dashboard
    const controller = new AbortController();
    const isDashboardCall = endpoint.includes('/opportunities') || endpoint.includes('/stats') || endpoint.includes('/sync/status')
    const timeoutDuration = isDashboardCall ? 15000 : 30000; // 15s for dashboard, 30s for others
    const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      signal: controller.signal,
      ...options,
    }

    try {
      console.log(`API Base URL: ${this.baseURL}`)
      console.log(`Making API request to: ${url}`)
      const response = await fetch(url, config)
      console.log(`API response for ${endpoint}:`, response.status, response.statusText)
      
      // Clear the timeout
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (parseError) {
          console.error('Could not parse error response:', parseError);
        }
        throw new Error(errorMessage);
      }

      const data = await response.json()
      console.log(`API data for ${endpoint}:`, data)
      return data
    } catch (error) {
      // Clear the timeout
      clearTimeout(timeoutId)
      
      if (error.name === 'AbortError') {
        console.error(`Request timeout for ${endpoint}`)
        throw new Error(`Request timed out after ${timeoutDuration/1000} seconds`)
      }
      
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Opportunities endpoints
  async getOpportunities(params = {}) {
    const queryString = new URLSearchParams(params).toString()
    return this.request(`/api/opportunities-working${queryString ? `?${queryString}` : ''}`)
  }

  // Optimized endpoint for dashboard - loads minimal data
  async getDashboardOpportunities(params = { per_page: 20 }) {
    const queryString = new URLSearchParams(params).toString()
    return this.request(`/api/opportunities-working${queryString ? `?${queryString}` : ''}`)
  }

  async getOpportunity(id) {
    return this.request(`/api/opportunities/${id}`)
  }

  async searchOpportunities(searchData) {
    return this.request('/opportunities/search', {
      method: 'POST',
      body: JSON.stringify(searchData),
    })
  }

  async getOpportunityStats() {
    return this.request('/opportunities/stats')
  }

  async getScoreExplanation(id, keywords = []) {
    const queryString = keywords.length > 0 ? `?keywords=${keywords.join(',')}` : ''
    return this.request(`/api/opportunities/${id}/score-explanation${queryString}`)
  }

  // Sync endpoints
  async syncData() {
    return this.request('/sync', { method: 'POST' })
  }

  async getSyncStatus() {
    return this.request('/sync/status')
  }

  // Scraping endpoints
  async getScrapingSources() {
    return this.request('/scraping/sources')
  }

  async scrapeSource(sourceKey) {
    return this.request('/scraping/scrape-source', {
      method: 'POST',
      body: JSON.stringify({ source_key: sourceKey }),
    })
  }

  async scrapeCustomUrl(url, sourceName = 'Custom') {
    return this.request('/scraping/scrape-url', {
      method: 'POST',
      body: JSON.stringify({ url, source_name: sourceName }),
    })
  }

  async syncAllScraping() {
    return this.request('/scraping/sync-all', { method: 'POST' })
  }

  async testFirecrawl(url = 'https://example.com') {
    return this.request('/scraping/test', {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  }

  // Perplexity AI endpoints
  async searchFinancialData(query) {
    return this.request('/perplexity/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  }

  async getMarketAnalysis() {
    return this.request('/perplexity/market-analysis')
  }

  async getFinancialMetrics() {
    return this.request('/perplexity/financial-metrics')
  }

  async predictOpportunities(sector = null) {
    const params = sector ? `?sector=${encodeURIComponent(sector)}` : ''
    return this.request(`/perplexity/predict-opportunities${params}`)
  }

  async getPerplexityStatus() {
    return this.request('/perplexity/status')
  }

  // Advanced Perplexity AI Intelligence endpoints
  async enrichOpportunity(opportunity) {
    return this.request('/perplexity/enrich-opportunity', {
      method: 'POST',
      body: JSON.stringify({ opportunity }),
    })
  }

  async scoreOpportunity(opportunity, userProfile = null) {
    return this.request('/perplexity/score-opportunity', {
      method: 'POST',
      body: JSON.stringify({ 
        opportunity, 
        user_profile: userProfile 
      }),
    })
  }

  async analyzeCompetitiveLandscape(naicsCodes, agency, timeframe = '2years') {
    return this.request('/perplexity/competitive-landscape', {
      method: 'POST',
      body: JSON.stringify({ 
        naics_codes: naicsCodes,
        agency: agency,
        timeframe: timeframe
      }),
    })
  }

  async bulkEnrichOpportunities(opportunityIds) {
    return this.request('/perplexity/bulk-enrich', {
      method: 'POST',
      body: JSON.stringify({ opportunity_ids: opportunityIds }),
    })
  }

  async analyzeCompliance(opportunity) {
    return this.request('/perplexity/compliance-analysis', {
      method: 'POST',
      body: JSON.stringify({ opportunity }),
    })
  }

  async generateSmartAlerts(userProfile = null) {
    return this.request('/perplexity/smart-alerts', {
      method: 'POST',
      body: JSON.stringify({ user_profile: userProfile }),
    })
  }

  async analyzeMarketTrends(timeframe = '6months', focusAreas = []) {
    return this.request('/perplexity/trend-analysis', {
      method: 'POST',
      body: JSON.stringify({ 
        timeframe: timeframe,
        focus_areas: focusAreas 
      }),
    })
  }

  async forecastMarketConditions(horizon = '12months') {
    return this.request('/perplexity/market-forecast', {
      method: 'POST',
      body: JSON.stringify({ horizon: horizon }),
    })
  }
}

// Create and export API client instance
export const apiClient = new ApiClient()

// Utility functions for data formatting
export const formatCurrency = (amount) => {
  if (!amount) return 'N/A'
  
  if (amount >= 1000000000) {
    return `$${(amount / 1000000000).toFixed(1)}B`
  } else if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`
  } else if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`
  } else {
    return `$${amount.toLocaleString()}`
  }
}

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid Date'
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (error) {
    console.error('Date formatting error:', error)
    return 'Invalid Date'
  }
}

export const formatRelativeDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    // Parse date and handle timezone issues
    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid Date'
    }
    
    const now = new Date()
    
    // Calculate diff in milliseconds and convert to days
    const diffTime = date.getTime() - now.getTime()
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 0) {
      if (diffDays === -1) {
        return 'Yesterday'
      }
      return `${Math.abs(diffDays)} days ago`
    } else if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return 'Tomorrow'
    } else if (diffDays <= 7) {
      return `In ${diffDays} days`
    } else if (diffDays <= 30) {
      return `In ${Math.ceil(diffDays / 7)} weeks`
    } else {
      return `In ${Math.ceil(diffDays / 30)} months`
    }
  } catch (error) {
    console.error('Date formatting error:', error)
    return 'Invalid Date'
  }
}

export const getScoreColor = (score) => {
  if (score >= 90) return 'text-green-600 dark:text-green-400'
  if (score >= 80) return 'text-blue-600 dark:text-blue-400'
  if (score >= 70) return 'text-yellow-600 dark:text-yellow-400'
  if (score >= 60) return 'text-orange-600 dark:text-orange-400'
  return 'text-red-600 dark:text-red-400'
}

export const getScoreBadgeColor = (score) => {
  if (score >= 90) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  if (score >= 80) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  if (score >= 70) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  if (score >= 60) return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
  return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
}

export const getUrgencyColor = (dueDate) => {
  if (!dueDate) return 'text-gray-500'
  
  try {
    const date = new Date(dueDate)
    const now = new Date()
    const diffTime = date - now
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 0) return 'text-red-600 dark:text-red-400'
    if (diffDays <= 7) return 'text-red-600 dark:text-red-400'
    if (diffDays <= 14) return 'text-orange-600 dark:text-orange-400'
    if (diffDays <= 30) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-green-600 dark:text-green-400'
  } catch (error) {
    return 'text-gray-500'
  }
}

export const getSourceTypeLabel = (sourceType) => {
  const labels = {
    'federal_contract': 'Federal Contract',
    'federal_grant': 'Federal Grant',
    'state_rfp': 'State RFP',
    'private_rfp': 'Private RFP',
    'scraped': 'Web Scraped'
  }
  return labels[sourceType] || sourceType
}

export const getSourceTypeColor = (sourceType) => {
  const colors = {
    'federal_contract': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    'federal_grant': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'state_rfp': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    'private_rfp': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    'scraped': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }
  return colors[sourceType] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
}

