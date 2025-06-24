import posthog from 'posthog-js'

// Initialize PostHog
const initAnalytics = () => {
  const apiKey = import.meta.env.VITE_POSTHOG_KEY
  const host = import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com'
  const enabled = import.meta.env.VITE_POSTHOG_ENABLED === 'true'

  if (enabled && apiKey) {
    posthog.init(apiKey, {
      api_host: host,
      person_profiles: 'identified_only',
      capture_pageview: true,
      capture_pageleave: true,
      autocapture: false, // Disable for privacy
      session_recording: false, // Disable for privacy
      loaded: (posthog) => {
        console.log('PostHog analytics initialized successfully')
      }
    })
  } else {
    console.log('PostHog analytics disabled or missing API key')
  }
}

// Analytics wrapper functions
export const analytics = {
  // Initialize PostHog
  init: initAnalytics,

  // Track page views
  trackPage: (pageName, properties = {}) => {
    if (posthog.__loaded) {
      posthog.capture('$pageview', {
        page: pageName,
        ...properties
      })
    }
  },

  // Track custom events
  track: (eventName, properties = {}) => {
    if (posthog.__loaded) {
      posthog.capture(eventName, properties)
    }
  },

  // Identify user
  identify: (userId, userProperties = {}) => {
    if (posthog.__loaded) {
      posthog.identify(userId, userProperties)
    }
  },

  // Set user properties
  setUserProperties: (properties) => {
    if (posthog.__loaded) {
      posthog.people.set(properties)
    }
  },

  // Reset user (logout)
  reset: () => {
    if (posthog.__loaded) {
      posthog.reset()
    }
  },

  // Feature flags
  isFeatureEnabled: (flagKey) => {
    if (posthog.__loaded) {
      return posthog.isFeatureEnabled(flagKey)
    }
    return false
  },

  // Alias user (when user signs up)
  alias: (alias) => {
    if (posthog.__loaded) {
      posthog.alias(alias)
    }
  }
}

// Opportunity Dashboard specific tracking
export const opportunityAnalytics = {
  // Track opportunity interactions
  trackOpportunityView: (opportunityId, title) => {
    analytics.track('opportunity_viewed', {
      opportunity_id: opportunityId,
      opportunity_title: title,
      timestamp: new Date().toISOString()
    })
  },

  trackOpportunitySearch: (query, resultsCount) => {
    analytics.track('opportunity_search', {
      search_query: query,
      results_count: resultsCount,
      timestamp: new Date().toISOString()
    })
  },

  trackPerplexityQuery: (query, queryType) => {
    analytics.track('perplexity_query', {
      query: query,
      query_type: queryType,
      timestamp: new Date().toISOString()
    })
  },

  trackDashboardSection: (section) => {
    analytics.track('dashboard_section_viewed', {
      section: section,
      timestamp: new Date().toISOString()
    })
  },

  trackFilterUsage: (filterType, filterValue) => {
    analytics.track('filter_applied', {
      filter_type: filterType,
      filter_value: filterValue,
      timestamp: new Date().toISOString()
    })
  },

  trackComplianceCheck: (opportunityId, complianceScore) => {
    analytics.track('compliance_check', {
      opportunity_id: opportunityId,
      compliance_score: complianceScore,
      timestamp: new Date().toISOString()
    })
  }
}

export default analytics 