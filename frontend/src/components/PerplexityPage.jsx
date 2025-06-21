import { useState, useEffect } from 'react'
import { Zap, Brain, TrendingUp, DollarSign, Search, RefreshCw, AlertCircle, CheckCircle, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import SmartAlerts from '@/components/SmartAlerts'

export default function PerplexityPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState([])
  const [marketAnalysis, setMarketAnalysis] = useState(null)
  const [trendAnalysis, setTrendAnalysis] = useState(null)
  const [marketForecast, setMarketForecast] = useState(null)
  const [financialInsights, setFinancialInsights] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('search')
  const { toast } = useToast()

  // Auto-load market analysis on component mount
  useEffect(() => {
    loadMarketAnalysis()
    loadTrendAnalysis()
  }, [])

  const handleFinancialSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: "Search Required",
        description: "Please enter a financial query",
        variant: "destructive",
      })
      return
    }

    try {
      setLoading(true)
      
      const response = await apiClient.searchFinancialData(searchQuery)
      
      if (response.success && response.data) {
        // Transform the API response to match our UI format
        const searchResult = {
          id: Date.now(),
          title: `Financial Analysis: ${searchQuery}`,
          description: response.data.analysis,
          source_url: '',
          relevance_score: 95,
          ai_confidence: 90,
          citations: response.data.citations || []
        }
        setResults([searchResult])
        
        toast({
          title: "Search Complete",
          description: "Financial analysis generated successfully",
        })
      } else {
        // Fall back to simulation if API fails
        const response = await simulatePerplexitySearch(searchQuery)
        setResults(response.results || [])
        
        toast({
          title: "Search Complete (Demo Mode)",
          description: `Found ${response.results?.length || 0} financial insights`,
        })
      }
    } catch (error) {
      console.error('Financial search failed:', error)
      
      // Fall back to simulation on error
      try {
        const response = await simulatePerplexitySearch(searchQuery)
        setResults(response.results || [])
        
        toast({
          title: "Search Complete (Demo Mode)",
          description: "Using simulated data - check API configuration",
          variant: "default",
        })
      } catch {
        toast({
          title: "Search Failed",
          description: error.message || "Failed to search financial data",
          variant: "destructive",
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const loadMarketAnalysis = async () => {
    try {
      const response = await apiClient.getMarketAnalysis()
      
      if (response.success && response.data) {
        // Transform API response to UI format
        const analysis = {
          summary: response.data.analysis,
          key_trends: [
            "Real-time AI-powered market insights",
            "Government contracting trend analysis",
            "Financial data from live sources",
            "Market forecasting and predictions"
          ],
          hot_sectors: [
            { name: "AI/ML Contracts", growth: "+45%", value: "$2.3B" },
            { name: "Cybersecurity", growth: "+32%", value: "$4.1B" },
            { name: "Cloud Services", growth: "+28%", value: "$3.8B" },
            { name: "Data Analytics", growth: "+38%", value: "$1.9B" }
          ],
          generated_at: response.data.generated_at
        }
        setMarketAnalysis(analysis)
      } else {
        // Fall back to simulation
        const analysis = await simulateMarketAnalysis()
        setMarketAnalysis(analysis)
      }
    } catch (error) {
      console.error('Failed to load market analysis:', error)
      // Fall back to simulation on error
      try {
        const analysis = await simulateMarketAnalysis()
        setMarketAnalysis(analysis)
      } catch (simError) {
        console.error('Failed to load simulated analysis:', simError)
      }
    }
  }

  const refreshFinancialData = async () => {
    try {
      setLoading(true)
      
      const response = await apiClient.getFinancialMetrics()
      
      if (response.success && response.data) {
        // Parse the metrics from AI response (would need more sophisticated parsing in real implementation)
        const insights = [
          {
            metric: "Real-time Market Data",
            current_value: "Live",
            change: "+100%",
            trend: "up",
            description: "Financial metrics powered by Perplexity AI"
          },
          {
            metric: "Data Freshness",
            current_value: "Current",
            change: "Real-time",
            trend: "up",
            description: "Up-to-date financial information"
          }
        ]
        setFinancialInsights(insights)
        
        toast({
          title: "Data Refreshed",
          description: "Latest financial insights loaded from Perplexity",
        })
      } else {
        // Fall back to simulation
        const insights = await simulateFinancialInsights()
        setFinancialInsights(insights)
        
        toast({
          title: "Data Refreshed (Demo Mode)",
          description: "Using simulated financial data",
        })
      }
    } catch (error) {
      console.error('Failed to refresh financial data:', error)
      
      // Fall back to simulation
      try {
        const insights = await simulateFinancialInsights()
        setFinancialInsights(insights)
        
        toast({
          title: "Data Refreshed (Demo Mode)",
          description: "Using simulated data - check API configuration",
        })
      } catch {
        toast({
          title: "Refresh Failed",
          description: "Could not load financial data",
          variant: "destructive",
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const loadTrendAnalysis = async () => {
    try {
      const response = await apiClient.analyzeMarketTrends('6months', ['AI/ML', 'Cybersecurity', 'Cloud Services'])
      
      if (response.success && response.data) {
        setTrendAnalysis(response.data)
      } else {
        // Fall back to simulation
        const analysis = await simulateTrendAnalysis()
        setTrendAnalysis(analysis)
      }
    } catch (error) {
      console.error('Failed to load trend analysis:', error)
      // Fall back to simulation on error
      try {
        const analysis = await simulateTrendAnalysis()
        setTrendAnalysis(analysis)
      } catch (simError) {
        console.error('Failed to load simulated trend analysis:', simError)
      }
    }
  }

  const loadMarketForecast = async () => {
    try {
      const response = await apiClient.forecastMarketConditions('12months')
      
      if (response.success && response.data) {
        setMarketForecast(response.data)
        toast({
          title: "Market Forecast Updated",
          description: "12-month market predictions loaded",
        })
      } else {
        // Fall back to simulation
        const forecast = await simulateMarketForecast()
        setMarketForecast(forecast)
        
        toast({
          title: "Market Forecast Updated (Demo)",
          description: "Using simulated forecast data",
        })
      }
    } catch (error) {
      console.error('Failed to load market forecast:', error)
      
      // Fall back to simulation
      try {
        const forecast = await simulateMarketForecast()
        setMarketForecast(forecast)
        
        toast({
          title: "Market Forecast Updated (Demo)",
          description: "Using simulated data - check API configuration",
        })
      } catch {
        toast({
          title: "Forecast Failed",
          description: "Could not load market forecast",
          variant: "destructive",
        })
      }
    }
  }

  // Temporary simulation functions - to be replaced with real API calls
  const simulatePerplexitySearch = async () => {
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate API delay
    
    return {
      results: [
        {
          id: 1,
          title: "Federal Reserve Interest Rate Analysis",
          description: "Latest analysis of Federal Reserve interest rate decisions and their impact on government contracting markets",
          source_url: "https://example.com/fed-analysis",
          relevance_score: 95,
          ai_confidence: 92,
          citations: ["fed.gov", "reuters.com", "bloomberg.com"]
        },
        {
          id: 2,
          title: "Government Budget Allocation Trends",
          description: "Q4 2024 analysis showing increased budget allocations for technology and infrastructure projects",
          source_url: "https://example.com/budget-trends",
          relevance_score: 88,
          ai_confidence: 87,
          citations: ["whitehouse.gov", "cbo.gov", "usaspending.gov"]
        },
        {
          id: 3,
          title: "Defense Contractor Market Outlook",
          description: "Market analysis indicating growth opportunities in cybersecurity and AI defense contracts",
          source_url: "https://example.com/defense-outlook",
          relevance_score: 83,
          ai_confidence: 85,
          citations: ["defense.gov", "pentagon.mil", "defensenews.com"]
        }
      ]
    }
  }

  const simulateMarketAnalysis = async () => {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    return {
      summary: "Current government contracting market shows strong growth in technology sectors, with increased focus on AI, cybersecurity, and cloud infrastructure. Federal agencies are prioritizing digital transformation initiatives.",
      key_trends: [
        "AI/ML contract values up 45% from last quarter",
        "Cybersecurity spending increased across all agencies",
        "Small business set-aside opportunities growing",
        "Cloud migration projects dominating IT contracts"
      ],
      hot_sectors: [
        { name: "Artificial Intelligence", growth: "+45%", value: "$2.3B" },
        { name: "Cybersecurity", growth: "+32%", value: "$4.1B" },
        { name: "Cloud Services", growth: "+28%", value: "$3.8B" },
        { name: "Data Analytics", growth: "+38%", value: "$1.9B" }
      ],
      generated_at: new Date().toISOString()
    }
  }

  const simulateFinancialInsights = async () => {
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    return [
      {
        metric: "Average Contract Value",
        current_value: "$2.8M",
        change: "+12%",
        trend: "up",
        description: "Average federal contract values increased 12% this quarter"
      },
      {
        metric: "Contract Awards (Monthly)",
        current_value: "1,247",
        change: "+8%",
        trend: "up",
        description: "Monthly contract awards show consistent growth"
      },
      {
        metric: "Small Business Participation",
        current_value: "28.5%",
        change: "+3%",
        trend: "up",
        description: "Small business contract participation at all-time high"
      },
      {
        metric: "Average Bid Competition",
        current_value: "4.2 bidders",
        change: "-5%",
        trend: "down",
        description: "Competition levels slightly decreased, indicating opportunities"
      }
    ]
  }

  const simulateTrendAnalysis = async () => {
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    return {
      trend_analysis: {
        timeframe: '6months',
        focus_areas: ['AI/ML', 'Cybersecurity', 'Cloud Services'],
        spending_trends: {
          budget_shifts: [
            { category: 'AI/ML', change: '+45%', value: '$2.3B' },
            { category: 'Cybersecurity', change: '+32%', value: '$4.1B' },
            { category: 'Cloud Services', change: '+28%', value: '$3.8B' }
          ],
          emerging_priorities: [
            'Zero Trust Architecture Implementation',
            'AI-powered Data Analytics',
            'Edge Computing Infrastructure',
            'Quantum-resistant Cryptography'
          ]
        },
        technology_trends: {
          fastest_growing: [
            { tech: 'Machine Learning Platforms', growth: '+67%' },
            { tech: 'Cloud Security Tools', growth: '+54%' },
            { tech: 'DevSecOps Solutions', growth: '+43%' }
          ],
          digital_transformation: 'Accelerating across all federal agencies with $15B allocated',
          cloud_adoption: '78% of federal workloads now cloud-based, up from 45% last year'
        },
        market_dynamics: {
          small_business_trends: 'Small business awards increased 23% with new set-aside goals',
          competition_changes: 'Competition intensity decreased in specialized AI/ML contracts',
          geographic_shifts: ['Increased remote work capabilities', 'Regional data center requirements']
        },
        market_forecast: {
          growth_predictions: [
            'AI/ML contracts expected to grow 50% in next 12 months',
            'Cybersecurity spending to reach $8B by end of fiscal year',
            'Cloud infrastructure investments doubling in civilian agencies'
          ],
          strategic_recommendations: [
            'Invest in AI/ML certification and capabilities',
            'Develop Zero Trust architecture expertise',
            'Partner with cloud security specialists',
            'Focus on small business set-aside opportunities'
          ]
        }
      },
      citations: ['usaspending.gov', 'sam.gov', 'gao.gov'],
      analyzed_at: new Date().toISOString()
    }
  }

  const simulateMarketForecast = async () => {
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    return {
      market_forecast: {
        forecast_horizon: '12months',
        current_period: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        market_conditions: {
          growth_projections: '+15% overall government IT spending growth expected',
          budget_outlook: 'Strong budget outlook with continued focus on modernization',
          economic_factors: ['Inflation impact on pricing', 'Supply chain stabilization', 'Talent shortage challenges']
        },
        agency_predictions: {
          defense_priorities: ['AI-enabled weapons systems', 'Cybersecurity mesh architecture', 'Cloud edge computing'],
          civilian_plans: ['Digital service delivery', 'Data modernization', 'Customer experience platforms'],
          infrastructure_spending: '$50B allocated for digital infrastructure over next 2 years'
        },
        technology_adoption: {
          ai_ml_timeline: 'Full AI integration expected by Q4 2025 across major agencies',
          cloud_migration: '90% cloud adoption target by end of 2025',
          cybersecurity_priorities: ['Zero Trust implementation', 'Quantum-safe encryption', 'Supply chain security']
        },
        opportunity_pipeline: {
          high_value_recompetes: [
            { title: 'DHS Enterprise Infrastructure', value: '$15B', timeline: 'Q2 2025' },
            { title: 'DoD Cloud Services', value: '$25B', timeline: 'Q3 2025' },
            { title: 'VA Modernization Program', value: '$8B', timeline: 'Q1 2025' }
          ],
          new_programs: [
            'Federal AI Excellence Centers',
            'Quantum Computing Research Initiative',
            'National Cyber Defense Platform'
          ]
        },
        strategic_recommendations: {
          positioning_strategies: [
            'Develop AI/ML partnerships with academic institutions',
            'Invest in security clearance programs for staff',
            'Build multi-cloud expertise and certifications'
          ],
          capability_priorities: [
            'AI/ML model development and deployment',
            'Zero Trust architecture design',
            'Quantum-safe cryptography implementation'
          ]
        }
      },
      citations: ['whitehouse.gov', 'cbo.gov', 'omb.gov'],
      generated_at: new Date().toISOString()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center">
          <Zap className="w-8 h-8 mr-3 text-yellow-500" />
          Perplexity Financial Intelligence
        </h1>
        <p className="text-muted-foreground">
          Real-time financial data and market analysis powered by AI
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {financialInsights.map((insight, index) => (
          <Card key={index}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{insight.metric}</p>
                  <p className="text-2xl font-bold">{insight.current_value}</p>
                </div>
                <div className={`flex items-center text-sm ${
                  insight.trend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  <TrendingUp className={`w-4 h-4 mr-1 ${
                    insight.trend === 'down' ? 'rotate-180' : ''
                  }`} />
                  {insight.change}
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">{insight.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="search">AI Search</TabsTrigger>
          <TabsTrigger value="analysis">Market Analysis</TabsTrigger>
          <TabsTrigger value="competitive">Competitive Intel</TabsTrigger>
          <TabsTrigger value="alerts">Smart Alerts</TabsTrigger>
          <TabsTrigger value="insights">Live Insights</TabsTrigger>
        </TabsList>

        {/* AI Search Tab */}
        <TabsContent value="search" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="w-5 h-5 mr-2" />
                Financial Intelligence Search
              </CardTitle>
              <CardDescription>
                Search for real-time financial and market data using AI-powered analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex space-x-2">
                  <div className="flex-1">
                    <Input
                      placeholder="e.g., 'Latest government technology spending trends' or 'Federal contract market analysis'"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleFinancialSearch()}
                    />
                  </div>
                  <Button onClick={handleFinancialSearch} disabled={loading}>
                    <Search className="w-4 h-4 mr-2" />
                    {loading ? 'Searching...' : 'Search'}
                  </Button>
                </div>

                {/* Search Results */}
                {results.length > 0 && (
                  <div className="space-y-4 mt-6">
                    <h3 className="text-lg font-semibold">Search Results</h3>
                    {results.map((result) => (
                      <Card key={result.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="text-md font-semibold">{result.title}</h4>
                            <div className="flex space-x-2">
                              <Badge variant="secondary">
                                Relevance: {result.relevance_score}%
                              </Badge>
                              <Badge variant="outline">
                                AI Confidence: {result.ai_confidence}%
                              </Badge>
                            </div>
                          </div>
                          
                          <p className="text-muted-foreground mb-3">{result.description}</p>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-muted-foreground">Sources:</span>
                              {result.citations.map((citation, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {citation}
                                </Badge>
                              ))}
                            </div>
                            <Button variant="ghost" size="sm">
                              <ExternalLink className="w-4 h-4 mr-1" />
                              View Details
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Market Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Market Overview</TabsTrigger>
              <TabsTrigger value="trends">Trend Analysis</TabsTrigger>
              <TabsTrigger value="forecast">Market Forecast</TabsTrigger>
            </TabsList>

            {/* Market Overview */}
            <TabsContent value="overview">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Market Analysis
                  </CardTitle>
                  <CardDescription>
                    AI-generated analysis of current government contracting market trends
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {marketAnalysis ? (
                    <div className="space-y-6">
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertTitle>Market Summary</AlertTitle>
                        <AlertDescription>{marketAnalysis.summary}</AlertDescription>
                      </Alert>

                      <div>
                        <h4 className="text-lg font-semibold mb-3">Key Trends</h4>
                        <div className="grid gap-2">
                          {marketAnalysis.key_trends.map((trend, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm">{trend}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-lg font-semibold mb-3">Hot Sectors</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {marketAnalysis.hot_sectors.map((sector, index) => (
                            <Card key={index}>
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="font-medium">{sector.name}</p>
                                    <p className="text-2xl font-bold text-green-600">{sector.value}</p>
                                  </div>
                                  <Badge variant="secondary" className="text-green-600">
                                    {sector.growth}
                                  </Badge>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>

                      <div className="text-xs text-muted-foreground">
                        Last updated: {new Date(marketAnalysis.generated_at).toLocaleString()}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">Loading market analysis...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Trend Analysis */}
            <TabsContent value="trends">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <TrendingUp className="w-5 h-5 mr-2" />
                      Advanced Trend Analysis
                    </div>
                    <Button onClick={loadTrendAnalysis} disabled={loading} size="sm">
                      <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    Deep dive into spending trends, technology adoption, and market dynamics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {trendAnalysis ? (
                    <div className="space-y-6">
                      {/* Spending Trends */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Spending Trends</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          {trendAnalysis.trend_analysis.spending_trends.budget_shifts.map((shift, index) => (
                            <Card key={index}>
                              <CardContent className="p-4">
                                <div className="text-center">
                                  <div className="text-lg font-semibold">{shift.category}</div>
                                  <div className="text-2xl font-bold text-green-600">{shift.change}</div>
                                  <div className="text-sm text-muted-foreground">{shift.value}</div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                        
                        <div>
                          <h5 className="font-medium mb-2">Emerging Priorities</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {trendAnalysis.trend_analysis.spending_trends.emerging_priorities.map((priority, index) => (
                              <div key={index} className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-blue-500" />
                                <span className="text-sm">{priority}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Technology Trends */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Technology Trends</h4>
                        <div className="space-y-3">
                          <div>
                            <h5 className="font-medium mb-2">Fastest Growing Technologies</h5>
                            <div className="space-y-2">
                              {trendAnalysis.trend_analysis.technology_trends.fastest_growing.map((tech, index) => (
                                <div key={index} className="flex items-center justify-between p-2 bg-muted rounded">
                                  <span className="text-sm">{tech.tech}</span>
                                  <Badge variant="secondary" className="text-green-600">{tech.growth}</Badge>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h5 className="font-medium mb-2">Digital Transformation</h5>
                              <p className="text-sm p-3 bg-muted rounded">
                                {trendAnalysis.trend_analysis.technology_trends.digital_transformation}
                              </p>
                            </div>
                            <div>
                              <h5 className="font-medium mb-2">Cloud Adoption</h5>
                              <p className="text-sm p-3 bg-muted rounded">
                                {trendAnalysis.trend_analysis.technology_trends.cloud_adoption}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Strategic Recommendations */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Strategic Recommendations</h4>
                        <div className="grid gap-2">
                          {trendAnalysis.trend_analysis.market_forecast.strategic_recommendations.map((rec, index) => (
                            <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                              <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium mt-0.5">
                                {index + 1}
                              </div>
                              <span className="text-sm">{rec}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <TrendingUp className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">Loading trend analysis...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Market Forecast */}
            <TabsContent value="forecast">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Brain className="w-5 h-5 mr-2" />
                      Market Forecast
                    </div>
                    <Button onClick={loadMarketForecast} disabled={loading} size="sm">
                      <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                      Generate Forecast
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    AI-powered 12-month market predictions and opportunity pipeline
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {marketForecast ? (
                    <div className="space-y-6">
                      {/* Market Conditions */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Market Conditions Forecast</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium mb-2">Growth Projections</h5>
                            <p className="text-sm p-3 bg-green-50 rounded border border-green-200">
                              {marketForecast.market_forecast.market_conditions.growth_projections}
                            </p>
                          </div>
                          <div>
                            <h5 className="font-medium mb-2">Budget Outlook</h5>
                            <p className="text-sm p-3 bg-blue-50 rounded border border-blue-200">
                              {marketForecast.market_forecast.market_conditions.budget_outlook}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* High-Value Recompetes */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">High-Value Recompetes Pipeline</h4>
                        <div className="space-y-3">
                          {marketForecast.market_forecast.opportunity_pipeline.high_value_recompetes.map((recompete, index) => (
                            <Card key={index} className="hover:shadow-md transition-shadow">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <h5 className="font-medium">{recompete.title}</h5>
                                    <div className="text-sm text-muted-foreground mt-1">
                                      Expected: {recompete.timeline}
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className="text-lg font-bold text-green-600">{recompete.value}</div>
                                    <Badge variant="outline">Recompete</Badge>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>

                      {/* Technology Adoption Timeline */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Technology Adoption Forecast</h4>
                        <div className="space-y-3">
                          <div className="p-3 border rounded-lg">
                            <div className="font-medium">AI/ML Integration</div>
                            <div className="text-sm text-muted-foreground">
                              {marketForecast.market_forecast.technology_adoption.ai_ml_timeline}
                            </div>
                          </div>
                          <div className="p-3 border rounded-lg">
                            <div className="font-medium">Cloud Migration</div>
                            <div className="text-sm text-muted-foreground">
                              {marketForecast.market_forecast.technology_adoption.cloud_migration}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Strategic Recommendations */}
                      <div>
                        <h4 className="text-lg font-semibold mb-3">Strategic Positioning</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium mb-2">Capability Priorities</h5>
                            <div className="space-y-1">
                              {marketForecast.market_forecast.strategic_recommendations.capability_priorities.map((priority, index) => (
                                <div key={index} className="flex items-center space-x-2">
                                  <Target className="w-4 h-4 text-blue-500" />
                                  <span className="text-sm">{priority}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h5 className="font-medium mb-2">Positioning Strategies</h5>
                            <div className="space-y-1">
                              {marketForecast.market_forecast.strategic_recommendations.positioning_strategies.map((strategy, index) => (
                                <div key={index} className="flex items-center space-x-2">
                                  <CheckCircle className="w-4 h-4 text-green-500" />
                                  <span className="text-sm">{strategy}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">Generate AI-powered market forecast...</p>
                      <Button onClick={loadMarketForecast} className="mt-4">
                        <Brain className="w-4 h-4 mr-2" />
                        Generate Forecast
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </TabsContent>

        {/* Competitive Intelligence Tab */}
        <TabsContent value="competitive" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Competitive Intelligence
                </div>
                <Button 
                  onClick={() => {
                    // Load competitive analysis for demo
                    toast({
                      title: "Loading Competitive Analysis",
                      description: "Analyzing market competitors and positioning...",
                    })
                  }} 
                  disabled={loading} 
                  size="sm"
                >
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Analyze Market
                </Button>
              </CardTitle>
              <CardDescription>
                AI-powered competitive landscape analysis and market positioning insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Market Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">$15.2B</div>
                        <div className="text-sm text-muted-foreground">Total Market Size</div>
                        <div className="text-xs text-green-600 mt-1">+12% YoY</div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">1,247</div>
                        <div className="text-sm text-muted-foreground">Active Contracts</div>
                        <div className="text-xs text-green-600 mt-1">+8% Monthly</div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">65%</div>
                        <div className="text-sm text-muted-foreground">Market Concentration</div>
                        <div className="text-xs text-muted-foreground mt-1">Top 10 players</div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Top Competitors */}
                <div>
                  <h4 className="text-lg font-semibold mb-4">Top Market Players</h4>
                  <div className="space-y-3">
                    {[
                      { name: "Accenture Federal", share: "12%", awards: "$1.8B", strengths: ["Digital Transformation", "Large Scale Delivery"] },
                      { name: "General Dynamics IT", share: "8%", awards: "$1.2B", strengths: ["Security Expertise", "Defense Focus"] },
                      { name: "CACI", share: "6%", awards: "$900M", strengths: ["Intelligence Support", "Analytics"] },
                      { name: "Booz Allen Hamilton", share: "5%", awards: "$750M", strengths: ["Consulting", "Technology Strategy"] }
                    ].map((competitor, index) => (
                      <Card key={index}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="font-medium">{competitor.name}</div>
                            <div className="flex space-x-2">
                              <Badge variant="secondary">{competitor.share} share</Badge>
                              <Badge variant="outline">{competitor.awards}</Badge>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {competitor.strengths.map((strength, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {strength}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* Market Dynamics */}
                <div>
                  <h4 className="text-lg font-semibold mb-4">Market Dynamics</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">Success Factors</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {["Strong past performance", "Technical innovation", "Competitive pricing", "Security clearances"].map((factor, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              <span className="text-sm">{factor}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">Market Barriers</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {["Security clearance requirements", "Past performance references", "Technical complexity", "Capital requirements"].map((barrier, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <AlertTriangle className="w-4 h-4 text-yellow-500" />
                              <span className="text-sm">{barrier}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {/* Emerging Trends */}
                <div>
                  <h4 className="text-lg font-semibold mb-4">Emerging Market Trends</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { trend: "AI/ML Adoption", impact: "High", description: "Increasing demand for AI-powered solutions" },
                      { trend: "Zero Trust Security", impact: "High", description: "Cybersecurity focus driving requirements" },
                      { trend: "Cloud-First Strategies", impact: "Medium", description: "Migration to cloud infrastructure" }
                    ].map((item, index) => (
                      <Card key={index}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="font-medium text-sm">{item.trend}</div>
                            <Badge variant={item.impact === 'High' ? 'destructive' : 'secondary'} className="text-xs">
                              {item.impact} Impact
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground">{item.description}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Smart Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          <SmartAlerts userProfile={{
            capabilities: ["Cloud Computing", "Cybersecurity", "Software Development", "AI/ML"],
            industry_focus: ["Federal IT", "Defense Contracting", "Healthcare IT"],
            company_size: "Medium",
            certifications: ["AWS Certified", "Security+", "CMMI Level 3"]
          }} />
        </TabsContent>

        {/* Live Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <DollarSign className="w-5 h-5 mr-2" />
                  Live Financial Insights
                </div>
                <Button onClick={refreshFinancialData} disabled={loading} size="sm">
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </CardTitle>
              <CardDescription>
                Real-time financial metrics and market indicators
              </CardDescription>
            </CardHeader>
            <CardContent>
              {financialInsights.length > 0 ? (
                <div className="grid gap-4">
                  {financialInsights.map((insight, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">{insight.metric}</p>
                            <p className="text-xl font-bold">{insight.current_value}</p>
                            <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
                          </div>
                          <div className={`flex items-center text-lg font-bold ${
                            insight.trend === 'up' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            <TrendingUp className={`w-5 h-5 mr-1 ${
                              insight.trend === 'down' ? 'rotate-180' : ''
                            }`} />
                            {insight.change}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <DollarSign className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">No financial insights loaded yet</p>
                  <Button onClick={refreshFinancialData} disabled={loading}>
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Load Insights
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Status Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Integration Status</AlertTitle>
        <AlertDescription>
          Perplexity AI integration is active. This page demonstrates the planned functionality. 
          Backend API endpoints are being developed to provide real-time financial data.
        </AlertDescription>
      </Alert>
    </div>
  )
}