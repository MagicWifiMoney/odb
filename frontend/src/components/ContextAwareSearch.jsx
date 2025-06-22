/**
 * Context-Aware Search Component
 * Uses user context and history to improve search relevance and reduce redundant queries
 */
import { useState, useEffect, useRef } from 'react'
import { Search, History, Zap, Brain, DollarSign, Clock, Target, BookOpen, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  QUERY_TEMPLATES, 
  PRESET_QUERIES, 
  CATEGORIES,
  getTemplatesByCategory,
  buildQuery,
  estimateQueryCost 
} from '@/lib/perplexityTemplates'
import { usePerplexityCache } from '@/hooks/usePerplexityCache'

export default function ContextAwareSearch({ 
  onSearch, 
  onTemplateUse, 
  onTemplateSearch,
  userContext = {}, 
  searchHistory = [],
  query = '',
  onQueryChange,
  loading = false
}) {
  const [searchQuery, setSearchQuery] = useState(query)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [templateParams, setTemplateParams] = useState({})
  const [activeCategory, setActiveCategory] = useState('Market Research')
  const [contextSuggestions, setContextSuggestions] = useState([])
  const [smartSuggestions, setSmartSuggestions] = useState([])
  
  const { getCachedData, cacheStats, QUERY_TYPES } = usePerplexityCache()

  // Sync internal state with prop
  useEffect(() => {
    setSearchQuery(query)
  }, [query])

  // Analyze user context and generate smart suggestions
  useEffect(() => {
    generateContextSuggestions()
    generateSmartSuggestions()
  }, [userContext, searchHistory])

  const generateContextSuggestions = () => {
    const suggestions = []

    // Based on user's industry/sector
    if (userContext.industry) {
      suggestions.push({
        type: 'context',
        suggestion: `${userContext.industry} market trends`,
        template: 'SECTOR_DEEP_DIVE',
        reason: `Based on your ${userContext.industry} focus`,
        icon: '🎯'
      })
    }

    // Based on recent searches
    if (searchHistory.length > 0) {
      const recentTopics = extractTopics(searchHistory.slice(-5))
      recentTopics.forEach(topic => {
        suggestions.push({
          type: 'history',
          suggestion: `Update on ${topic}`,
          template: 'EMERGING_TRENDS',
          reason: 'Following up on recent search',
          icon: '🔄'
        })
      })
    }

    // Based on time of day/week
    const now = new Date()
    const dayOfWeek = now.getDay()
    const hour = now.getHours()

    if (dayOfWeek === 1 && hour < 12) { // Monday morning
      suggestions.push({
        type: 'timing',
        suggestion: 'Weekly market pulse',
        template: 'WEEKLY_REVIEW',
        reason: 'Monday morning briefing',
        icon: '📅'
      })
    }

    if (hour >= 9 && hour <= 11) { // Morning hours
      suggestions.push({
        type: 'timing',
        suggestion: 'Daily financial snapshot',
        template: 'FINANCIAL_SNAPSHOT',
        reason: 'Morning market check',
        icon: '☀️'
      })
    }

    setContextSuggestions(suggestions.slice(0, 4))
  }

  const generateSmartSuggestions = () => {
    const suggestions = []

    // Check for cached data that might be relevant
    const templates = Object.values(QUERY_TEMPLATES)
    templates.forEach(template => {
      const cached = getCachedData(template.category.toLowerCase().replace(' ', '_'), {})
      if (cached) {
        const age = Date.now() - (cached.timestamp || 0)
        const ageHours = age / (1000 * 60 * 60)
        
        if (ageHours > 2 && ageHours < 24) { // Suggest refresh if 2-24 hours old
          suggestions.push({
            type: 'refresh',
            suggestion: `Update ${template.name}`,
            template: template.id,
            reason: `Data is ${Math.round(ageHours)}h old`,
            icon: '🔄',
            cost: template.cost
          })
        }
      }
    })

    // Suggest complementary queries based on search patterns
    if (searchHistory.length > 2) {
      const patterns = analyzeSearchPatterns(searchHistory)
      patterns.forEach(pattern => {
        suggestions.push({
          type: 'pattern',
          suggestion: pattern.suggestion,
          template: pattern.template,
          reason: pattern.reason,
          icon: '🧠',
          cost: 'Smart'
        })
      })
    }

    setSmartSuggestions(suggestions.slice(0, 3))
  }

  const extractTopics = (searches) => {
    const topics = new Set()
    searches.forEach(search => {
      const words = search.query?.toLowerCase().split(' ') || []
      words.forEach(word => {
        if (word.length > 4 && !['analysis', 'market', 'government', 'contract'].includes(word)) {
          topics.add(word)
        }
      })
    })
    return Array.from(topics).slice(0, 3)
  }

  const analyzeSearchPatterns = (history) => {
    const patterns = []
    
    // Look for market research followed by competitive analysis
    const hasMarketResearch = history.some(h => h.category === 'Market Research')
    const hasCompetitive = history.some(h => h.category === 'Competitive Intelligence')
    
    if (hasMarketResearch && !hasCompetitive) {
      patterns.push({
        suggestion: 'Competitive landscape analysis',
        template: 'COMPETITOR_ANALYSIS',
        reason: 'Complete your market research'
      })
    }

    // Look for financial analysis followed by opportunity evaluation
    const hasFinancial = history.some(h => h.category === 'Financial Analysis')
    const hasOpportunity = history.some(h => h.category === 'Opportunity Analysis')
    
    if (hasFinancial && !hasOpportunity) {
      patterns.push({
        suggestion: 'Win probability assessment',
        template: 'WIN_PROBABILITY',
        reason: 'Evaluate specific opportunities'
      })
    }

    return patterns
  }

  const handleTemplateSelect = (templateId) => {
    const template = QUERY_TEMPLATES[templateId]
    if (!template) return

    setSelectedTemplate(template)
    setTemplateParams({})
    
    // Pre-fill parameters based on context
    const prefilled = {}
    if (template.params.includes('sector') && userContext.industry) {
      prefilled.sector = userContext.industry
    }
    if (template.params.includes('company') && userContext.company) {
      prefilled.company = userContext.company
    }
    if (template.params.includes('timeframe')) {
      prefilled.timeframe = 'past month'
    }
    
    setTemplateParams(prefilled)
  }

  const handleExecuteTemplate = () => {
    if (!selectedTemplate) return

    const builtQuery = buildQuery(selectedTemplate.id, templateParams)
    if (!builtQuery.isComplete) {
      alert('Please fill in all required parameters')
      return
    }

    const templateData = {
      template: selectedTemplate,
      params: templateParams,
      query: builtQuery.query,
      estimatedCost: estimateQueryCost(selectedTemplate.id)
    }

    // Use the new onTemplateSearch prop if available, fall back to onTemplateUse
    if (onTemplateSearch) {
      onTemplateSearch(templateData)
    } else if (onTemplateUse) {
      onTemplateUse(templateData)
    }
  }

  const handleQuickSearch = (suggestion) => {
    if (suggestion.template) {
      const template = QUERY_TEMPLATES[suggestion.template.toUpperCase()]
      if (template) {
        handleTemplateSelect(template.id)
        return
      }
    }

    setSearchQuery(suggestion.suggestion)
    if (onSearch) {
      onSearch(suggestion.suggestion)
    }
  }

  const CategoryTemplates = ({ category }) => {
    const templates = getTemplatesByCategory(category)
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {templates.map(template => (
          <Card 
            key={template.id} 
            className={`cursor-pointer transition-all duration-200 hover:shadow-md border-2 ${
              selectedTemplate?.id === template.id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleTemplateSelect(template.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">{template.icon}</span>
                <div className="flex-1">
                  <h4 className="font-semibold text-sm">{template.name}</h4>
                  <p className="text-xs text-gray-600 mt-1">{template.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      {template.cost}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      ~{template.estimatedTokens} tokens
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Smart Suggestions */}
      {(contextSuggestions.length > 0 || smartSuggestions.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Brain className="h-5 w-5" />
              Smart Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Context-based suggestions */}
              {contextSuggestions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Based on your profile:</h4>
                  <div className="flex flex-wrap gap-2">
                    {contextSuggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickSearch(suggestion)}
                        className="text-xs"
                      >
                        <span className="mr-1">{suggestion.icon}</span>
                        {suggestion.suggestion}
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {suggestion.reason}
                        </Badge>
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Smart pattern suggestions */}
              {smartSuggestions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended next steps:</h4>
                  <div className="flex flex-wrap gap-2">
                    {smartSuggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickSearch(suggestion)}
                        className="text-xs"
                      >
                        <span className="mr-1">{suggestion.icon}</span>
                        {suggestion.suggestion}
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {suggestion.reason}
                        </Badge>
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Manual Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Search className="h-5 w-5" />
            Custom Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Enter your custom query..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                onQueryChange?.(e.target.value)
              }}
              onKeyPress={(e) => e.key === 'Enter' && onSearch?.(searchQuery)}
              className="flex-1"
            />
            <Button 
              onClick={() => onSearch?.(searchQuery)} 
              disabled={!searchQuery.trim() || loading}
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Template Browser */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BookOpen className="h-5 w-5" />
            Query Templates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeCategory} onValueChange={setActiveCategory}>
            <TabsList className="grid grid-cols-3 lg:grid-cols-6 mb-4">
              {CATEGORIES.map(category => (
                <TabsTrigger key={category} value={category} className="text-xs">
                  {category.split(' ')[0]}
                </TabsTrigger>
              ))}
            </TabsList>

            {CATEGORIES.map(category => (
              <TabsContent key={category} value={category}>
                <CategoryTemplates category={category} />
              </TabsContent>
            ))}
          </Tabs>

          {/* Template Parameter Form */}
          {selectedTemplate && (
            <Card className="mt-6 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <span>{selectedTemplate.icon}</span>
                  {selectedTemplate.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {selectedTemplate.params.map(param => (
                    <div key={param}>
                      <Label htmlFor={param} className="text-sm font-medium">
                        {param.charAt(0).toUpperCase() + param.slice(1).replace('_', ' ')}
                      </Label>
                      <Input
                        id={param}
                        value={templateParams[param] || ''}
                        onChange={(e) => setTemplateParams(prev => ({
                          ...prev,
                          [param]: e.target.value
                        }))}
                        placeholder={`Enter ${param}...`}
                        className="mt-1"
                      />
                    </div>
                  ))}

                  <div className="flex items-center justify-between pt-4 border-t">
                    <div className="text-sm text-gray-600">
                      <span>Estimated cost: </span>
                      <Badge variant="outline">{selectedTemplate.cost}</Badge>
                    </div>
                    <Button onClick={handleExecuteTemplate}>
                      <Zap className="h-4 w-4 mr-2" />
                      Execute Query
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      {/* Cache Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <DollarSign className="h-5 w-5" />
            Cost Optimization
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">{cacheStats.hitRate}</div>
              <div className="text-sm text-gray-600">Cache Hit Rate</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">{cacheStats.estimatedSavings}</div>
              <div className="text-sm text-gray-600">Estimated Savings</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">{cacheStats.apiCalls}</div>
              <div className="text-sm text-gray-600">API Calls Made</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">{cacheStats.totalRequests}</div>
              <div className="text-sm text-gray-600">Total Requests</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 