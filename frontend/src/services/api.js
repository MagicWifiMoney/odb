/**
 * API Service Utilities
 * Centralized service for calling our intelligence backend APIs
 */

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.rfptracking.com' 
  : 'http://localhost:5002'

class APIError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

/**
 * Generic API request handler with error handling and retries
 */
async function apiRequest(endpoint, options = {}) {
  const config = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
    const data = await response.json()

    if (!response.ok) {
      throw new APIError(
        data.error || `HTTP ${response.status}`,
        response.status,
        data
      )
    }

    return data
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(`Network error: ${error.message}`, 0, null)
  }
}

/**
 * Fast-Fail Filter API
 */
export const fastFailAPI = {
  // Assess single opportunity
  assessOpportunity: async (opportunityId, companyId = null, forceRefresh = false) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    if (forceRefresh) params.append('force_refresh', 'true')
    
    return apiRequest(`/api/fast-fail/assess/${opportunityId}?${params}`)
  },

  // Batch assess multiple opportunities
  batchAssess: async (opportunityIds, companyId = null) => {
    return apiRequest('/api/fast-fail/batch-assess', {
      method: 'POST',
      body: JSON.stringify({
        opportunity_ids: opportunityIds,
        company_id: companyId
      })
    })
  },

  // Get dashboard data
  getDashboard: async (companyId = null) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    
    return apiRequest(`/api/fast-fail/dashboard?${params}`)
  },

  // Get filter rules
  getRules: async (enabledOnly = true, ruleType = null, priority = null) => {
    const params = new URLSearchParams()
    if (enabledOnly) params.append('enabled_only', 'true')
    if (ruleType) params.append('rule_type', ruleType)
    if (priority) params.append('priority', priority)
    
    return apiRequest(`/api/fast-fail/rules?${params}`)
  },

  // Update filter rule
  updateRule: async (ruleId, updates) => {
    return apiRequest(`/api/fast-fail/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    })
  },

  // Get filter recommendations
  getRecommendations: async (companyId = null, daysBack = 30) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    params.append('days_back', daysBack.toString())
    
    return apiRequest(`/api/fast-fail/recommendations?${params}`)
  },

  // Get filter statistics
  getStatistics: async () => {
    return apiRequest('/api/fast-fail/statistics')
  },

  // Health check
  healthCheck: async () => {
    return apiRequest('/api/fast-fail/health')
  }
}

/**
 * Win Probability API
 */
export const winProbabilityAPI = {
  // Predict win probability for opportunity
  predict: async (opportunityId, companyId = null) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    
    return apiRequest(`/api/win-probability/predict/${opportunityId}?${params}`)
  },

  // Batch predictions
  batchPredict: async (opportunityIds, companyId = null) => {
    return apiRequest('/api/win-probability/batch-predict', {
      method: 'POST',
      body: JSON.stringify({
        opportunity_ids: opportunityIds,
        company_id: companyId
      })
    })
  },

  // Get dashboard
  getDashboard: async (companyId = null) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    
    return apiRequest(`/api/win-probability/dashboard?${params}`)
  },

  // Health check
  healthCheck: async () => {
    return apiRequest('/api/win-probability/health')
  }
}

/**
 * Compliance Matrix API
 */
export const complianceAPI = {
  // Analyze opportunity compliance
  analyze: async (opportunityId, companyId = null, forceRefresh = false) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    if (forceRefresh) params.append('force_refresh', 'true')
    
    return apiRequest(`/api/compliance/analyze/${opportunityId}?${params}`)
  },

  // Get compliance summary
  getSummary: async (companyId = null, daysBack = 30) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    params.append('days_back', daysBack.toString())
    
    return apiRequest(`/api/compliance/summary?${params}`)
  },

  // Get gaps report
  getGapsReport: async (companyId = null, format = 'json') => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    params.append('format', format)
    
    return apiRequest(`/api/compliance/gaps-report?${params}`)
  },

  // Get readiness score
  getReadinessScore: async (companyId = null, categories = null) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    if (categories) params.append('categories', categories.join(','))
    
    return apiRequest(`/api/compliance/readiness-score?${params}`)
  },

  // Get dashboard
  getDashboard: async (companyId = null, timeframe = 30) => {
    const params = new URLSearchParams()
    if (companyId) params.append('company_id', companyId)
    params.append('timeframe', timeframe.toString())
    
    return apiRequest(`/api/compliance/dashboard?${params}`)
  },

  // Health check
  healthCheck: async () => {
    return apiRequest('/api/compliance/health')
  }
}

/**
 * Trend Analysis API
 */
export const trendAPI = {
  // Get daily trends
  getDailyTrends: async (daysBack = 30, categories = null) => {
    const params = new URLSearchParams()
    params.append('days_back', daysBack.toString())
    if (categories) params.append('categories', categories.join(','))
    
    return apiRequest(`/api/trends/daily?${params}`)
  },

  // Get anomalies
  getAnomalies: async (daysBack = 7, threshold = 0.8) => {
    const params = new URLSearchParams()
    params.append('days_back', daysBack.toString())
    params.append('threshold', threshold.toString())
    
    return apiRequest(`/api/trends/anomalies?${params}`)
  },

  // Get dashboard
  getDashboard: async (timeframe = 30) => {
    const params = new URLSearchParams()
    params.append('timeframe', timeframe.toString())
    
    return apiRequest(`/api/trends/dashboard?${params}`)
  },

  // Health check
  healthCheck: async () => {
    return apiRequest('/api/trends/health')
  }
}

/**
 * Health check for all services
 */
export const healthCheckAll = async () => {
  const services = [
    { name: 'fast-fail', check: fastFailAPI.healthCheck },
    { name: 'win-probability', check: winProbabilityAPI.healthCheck },
    { name: 'compliance', check: complianceAPI.healthCheck },
    { name: 'trends', check: trendAPI.healthCheck }
  ]

  const results = await Promise.allSettled(
    services.map(async (service) => {
      try {
        const result = await service.check()
        return { name: service.name, status: 'healthy', data: result }
      } catch (error) {
        return { name: service.name, status: 'unhealthy', error: error.message }
      }
    })
  )

  return results.map((result, index) => ({
    name: services[index].name,
    ...result.value
  }))
}

/**
 * Utility function to handle API errors gracefully
 */
export const handleAPIError = (error, toast, defaultMessage = 'An error occurred') => {
  console.error('API Error:', error)
  
  const message = error instanceof APIError 
    ? error.message 
    : defaultMessage

  if (toast) {
    toast({
      title: "Error",
      description: message,
      variant: "destructive",
    })
  }
  
  return message
}