/**
 * Perplexity Query Templates & Presets
 * Pre-built queries for common use cases to improve efficiency and reduce costs
 */

export const QUERY_TEMPLATES = {
  // Quick Market Research Templates
  MARKET_OVERVIEW: {
    id: 'market_overview',
    name: 'Market Overview',
    category: 'Market Research',
    description: 'Get a quick overview of government contracting market',
    icon: '📊',
    template: `Provide a concise government contracting market overview for {timeframe}:
- Total market size and growth
- Top 3 spending agencies
- Fastest growing sectors
- Average contract values
- Key trends affecting procurement

Focus on actionable insights with specific numbers.`,
    params: ['timeframe'],
    cost: 'Low ($0.02-0.04)',
    estimatedTokens: 400
  },

  SECTOR_DEEP_DIVE: {
    id: 'sector_deep_dive',
    name: 'Sector Analysis',
    category: 'Market Research',
    description: 'Deep dive into specific industry sectors',
    icon: '🎯',
    template: `Analyze the {sector} sector in government contracting for {timeframe}:
- Market size and growth trends
- Major contract awards and values
- Key agencies and departments
- Competition landscape
- Procurement patterns and cycles
- Upcoming opportunities
- Required capabilities and certifications

Provide specific data points and strategic recommendations.`,
    params: ['sector', 'timeframe'],
    cost: 'Medium ($0.04-0.07)',
    estimatedTokens: 600
  },

  // Competitive Intelligence Templates
  COMPETITOR_ANALYSIS: {
    id: 'competitor_analysis',
    name: 'Competitor Analysis',
    category: 'Competitive Intelligence',
    description: 'Analyze competitors in your space',
    icon: '🥊',
    template: `Analyze competitors for {company} in government contracting:
- Top competitors by contract wins
- Average contract values and types
- Win rates and performance
- Partnerships and team arrangements
- Recent wins and losses
- Pricing strategies
- Capability gaps and opportunities

Focus on actionable competitive intelligence.`,
    params: ['company'],
    cost: 'High ($0.06-0.10)',
    estimatedTokens: 800
  },

  WIN_PROBABILITY: {
    id: 'win_probability',
    name: 'Win Probability',
    category: 'Opportunity Analysis',
    description: 'Assess chances of winning specific opportunities',
    icon: '🎲',
    template: `Assess win probability for {opportunity_title}:
- Historical similar contract awards
- Typical incumbent advantages
- Requirements alignment with market capabilities
- Competition level and key players
- Agency preferences and patterns
- Pricing expectations
- Risk factors

Provide percentage estimate with reasoning.`,
    params: ['opportunity_title'],
    cost: 'Medium ($0.04-0.06)',
    estimatedTokens: 500
  },

  // Quick Financial Checks
  FINANCIAL_SNAPSHOT: {
    id: 'financial_snapshot',
    name: 'Financial Snapshot',
    category: 'Financial Analysis',
    description: 'Quick financial metrics overview',
    icon: '💰',
    template: `Current government contracting financial snapshot:
- This month's total awards vs last month
- Average contract value trends
- Small business participation rates
- Fastest growing spending categories
- Budget execution by major agencies

Provide current numbers with month-over-month changes.`,
    params: [],
    cost: 'Low ($0.02-0.03)',
    estimatedTokens: 300
  },

  SPENDING_TRENDS: {
    id: 'spending_trends',
    name: 'Spending Trends',
    category: 'Financial Analysis',
    description: 'Analyze government spending patterns',
    icon: '📈',
    template: `Analyze government spending trends for {timeframe}:
- Total spending by agency and department
- Year-over-year growth by category
- Contract type distribution (IDIQs, BOAs, etc.)
- Geographic distribution
- Small business vs large business splits
- Emergency/supplemental spending impacts

Include specific dollar amounts and percentages.`,
    params: ['timeframe'],
    cost: 'Medium ($0.03-0.05)',
    estimatedTokens: 500
  },

  // Compliance & Requirements
  COMPLIANCE_CHECK: {
    id: 'compliance_check',
    name: 'Compliance Requirements',
    category: 'Compliance',
    description: 'Check compliance requirements for opportunities',
    icon: '✅',
    template: `Analyze compliance requirements for {opportunity_type}:
- Security clearance requirements
- Certifications needed (ISO, CMMI, etc.)
- Small business set-aside eligibility
- Insurance and bonding requirements
- Past performance standards
- Financial capability thresholds
- Technical qualification criteria

Provide checklist format with specific requirements.`,
    params: ['opportunity_type'],
    cost: 'Low ($0.02-0.04)',
    estimatedTokens: 400
  },

  // Trend Analysis
  EMERGING_TRENDS: {
    id: 'emerging_trends',
    name: 'Emerging Trends',
    category: 'Trend Analysis',
    description: 'Identify emerging trends and opportunities',
    icon: '🚀',
    template: `Identify emerging trends in government contracting for {timeframe}:
- New technology adoptions (AI, cloud, cybersecurity)
- Policy changes affecting procurement
- Budget allocation shifts
- New program launches
- Changing vendor preferences
- Innovation initiatives
- Regulatory impacts

Focus on actionable opportunities for contractors.`,
    params: ['timeframe'],
    cost: 'Medium ($0.04-0.06)',
    estimatedTokens: 600
  }
}

export const PRESET_QUERIES = {
  // Daily Quick Checks (5-minute routine)
  DAILY_PULSE: [
    {
      template: QUERY_TEMPLATES.FINANCIAL_SNAPSHOT,
      params: {},
      priority: 'high'
    }
  ],

  // Weekly Market Review (15-minute routine)
  WEEKLY_REVIEW: [
    {
      template: QUERY_TEMPLATES.MARKET_OVERVIEW,
      params: { timeframe: 'past week' },
      priority: 'high'
    },
    {
      template: QUERY_TEMPLATES.EMERGING_TRENDS,
      params: { timeframe: 'past month' },
      priority: 'medium'
    }
  ],

  // Monthly Deep Dive (30-minute analysis)
  MONTHLY_ANALYSIS: [
    {
      template: QUERY_TEMPLATES.SPENDING_TRENDS,
      params: { timeframe: 'past month' },
      priority: 'high'
    },
    {
      template: QUERY_TEMPLATES.SECTOR_DEEP_DIVE,
      params: { sector: 'user_defined', timeframe: 'past quarter' },
      priority: 'high'
    },
    {
      template: QUERY_TEMPLATES.COMPETITOR_ANALYSIS,
      params: { company: 'user_defined' },
      priority: 'medium'
    }
  ],

  // Opportunity Evaluation (when analyzing specific RFPs)
  OPPORTUNITY_EVAL: [
    {
      template: QUERY_TEMPLATES.WIN_PROBABILITY,
      params: { opportunity_title: 'user_defined' },
      priority: 'high'
    },
    {
      template: QUERY_TEMPLATES.COMPLIANCE_CHECK,
      params: { opportunity_type: 'user_defined' },
      priority: 'high'
    },
    {
      template: QUERY_TEMPLATES.COMPETITOR_ANALYSIS,
      params: { company: 'related_to_opportunity' },
      priority: 'medium'
    }
  ]
}

export const COST_ESTIMATES = {
  LOW: { min: 0.02, max: 0.04, tokens: '300-400' },
  MEDIUM: { min: 0.04, max: 0.07, tokens: '500-600' },
  HIGH: { min: 0.06, max: 0.10, tokens: '700-900' }
}

export const USAGE_RECOMMENDATIONS = {
  BEGINNER: {
    recommended_templates: ['FINANCIAL_SNAPSHOT', 'MARKET_OVERVIEW', 'COMPLIANCE_CHECK'],
    budget_per_day: '$0.20-0.40',
    frequency: 'Start with daily pulse, add weekly reviews'
  },
  INTERMEDIATE: {
    recommended_templates: ['SECTOR_DEEP_DIVE', 'WIN_PROBABILITY', 'SPENDING_TRENDS'],
    budget_per_day: '$0.50-1.00',
    frequency: 'Daily + weekly + monthly analysis'
  },
  ADVANCED: {
    recommended_templates: ['COMPETITOR_ANALYSIS', 'EMERGING_TRENDS', 'OPPORTUNITY_EVAL'],
    budget_per_day: '$1.00-2.00',
    frequency: 'Full preset workflows + custom queries'
  }
}

// Utility functions
export function getTemplatesByCategory(category) {
  return Object.values(QUERY_TEMPLATES).filter(template => template.category === category)
}

export function estimateQueryCost(templateId, complexity = 'medium') {
  const template = QUERY_TEMPLATES[templateId]
  if (!template) return null

  const multipliers = { low: 0.8, medium: 1.0, high: 1.3 }
  const baseCost = template.estimatedTokens * 0.0001 // rough estimate
  
  return {
    estimatedCost: (baseCost * multipliers[complexity]).toFixed(4),
    tokens: Math.round(template.estimatedTokens * multipliers[complexity]),
    complexity
  }
}

export function buildQuery(templateId, params = {}) {
  const template = QUERY_TEMPLATES[templateId]
  if (!template) return null

  let query = template.template
  
  // Replace parameter placeholders
  Object.entries(params).forEach(([key, value]) => {
    const placeholder = `{${key}}`
    query = query.replace(new RegExp(placeholder, 'g'), value)
  })

  // Check for remaining placeholders
  const remainingPlaceholders = query.match(/{[^}]+}/g) || []
  
  return {
    query,
    templateId,
    params,
    cost: template.cost,
    category: template.category,
    remainingPlaceholders,
    isComplete: remainingPlaceholders.length === 0
  }
}

export function getPresetWorkflow(presetId) {
  const preset = PRESET_QUERIES[presetId]
  if (!preset) return null

  return preset.map(item => ({
    ...item,
    estimatedCost: estimateQueryCost(item.template.id),
    query: buildQuery(item.template.id, item.params)
  }))
}

export const CATEGORIES = [
  'Market Research',
  'Competitive Intelligence', 
  'Opportunity Analysis',
  'Financial Analysis',
  'Compliance',
  'Trend Analysis'
] 