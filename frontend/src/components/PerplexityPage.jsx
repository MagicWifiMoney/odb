import React, { useState, useEffect } from 'react'
import { Brain, TrendingUp, Target, Users, Zap, Search, Loader2, FileText, Calendar, Award, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '../hooks/use-toast'
import { apiClient } from '../lib/api'

export default function PerplexityPage() {
  // Market Intelligence Search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [loading, setLoading] = useState(false)
  
  // Real Opportunities Data
  const [opportunities, setOpportunities] = useState([])
  const [selectedOpportunityId, setSelectedOpportunityId] = useState('')
  const [selectedOpportunityObj, setSelectedOpportunityObj] = useState(null)
  const [loadingOpportunities, setLoadingOpportunities] = useState(false)
  const [opportunitySearch, setOpportunitySearch] = useState('')
  
  // Opportunity Analysis
  const [enrichmentResult, setEnrichmentResult] = useState(null)
  const [scoringResult, setScoringResult] = useState(null)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  
  // Competitive Analysis
  const [naicsCodes, setNaicsCodes] = useState('')
  const [agency, setAgency] = useState('')
  const [timeframe, setTimeframe] = useState('2years')
  const [competitiveResult, setCompetitiveResult] = useState(null)
  const [loadingCompetitive, setLoadingCompetitive] = useState(false)
  
  // Smart Alerts & Forecasting
  const [userProfile, setUserProfile] = useState({ industry: '', company_size: '', focus: '' })
  const [alertsResult, setAlertsResult] = useState(null)
  const [forecastResult, setForecastResult] = useState(null)
  const [forecastHorizon, setForecastHorizon] = useState('12months')
  const [loadingAlerts, setLoadingAlerts] = useState(false)
  const [loadingForecast, setLoadingForecast] = useState(false)
  
  // Compliance Analysis
  const [complianceOpportunity, setComplianceOpportunity] = useState('')
  const [complianceResult, setComplianceResult] = useState(null)
  const [loadingCompliance, setLoadingCompliance] = useState(false)
  
  const { toast } = useToast()

  // Fetch real opportunities data
  const fetchOpportunities = async () => {
    setLoadingOpportunities(true)
    try {
      const params = { per_page: 100 }
      if (opportunitySearch.trim()) {
        params.search = opportunitySearch
      }
      
      const result = await apiClient.getOpportunities(params)
      setOpportunities(result.opportunities || [])
    } catch (error) {
      console.error('Failed to fetch opportunities:', error)
      toast({
        title: "Error",
        description: "Failed to load opportunities",
        variant: "destructive",
      })
    } finally {
      setLoadingOpportunities(false)
    }
  }

  // Handle opportunity selection
  const handleOpportunitySelect = async (opportunityId) => {
    setSelectedOpportunityId(opportunityId)
    
    if (opportunityId) {
      try {
        const opportunity = opportunities.find(opp => opp.id.toString() === opportunityId)
        setSelectedOpportunityObj(opportunity)
      } catch (error) {
        console.error('Failed to set selected opportunity:', error)
      }
    } else {
      setSelectedOpportunityObj(null)
    }
  }

  // Load opportunities on component mount
  useEffect(() => {
    fetchOpportunities()
  }, [])

  // Refresh opportunities when search changes (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (opportunitySearch !== '') {
        fetchOpportunities()
      }
    }, 500)
    
    return () => clearTimeout(timer)
  }, [opportunitySearch])

  // Market Intelligence Search
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: "Error",
        description: "Please enter a search query",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    try {
      const result = await apiClient.searchFinancialData(searchQuery)
      setSearchResult(result)
      toast({
        title: "Analysis Complete",
        description: "AI market intelligence generated successfully",
      })
    } catch (error) {
      console.error('Search failed:', error)
      toast({
        title: "Search Failed",
        description: error.message || "Failed to generate analysis",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Opportunity Enrichment
  const handleEnrichOpportunity = async () => {
    if (!selectedOpportunityObj) {
      toast({
        title: "Error",
        description: "Please select an opportunity to analyze",
        variant: "destructive",
      })
      return
    }

    setLoadingAnalysis(true)
    try {
      const result = await apiClient.enrichOpportunity(selectedOpportunityObj)
      setEnrichmentResult(result)
      toast({
        title: "Enrichment Complete",
        description: "AI opportunity analysis generated successfully",
      })
    } catch (error) {
      console.error('Enrichment failed:', error)
      toast({
        title: "Enrichment Failed",
        description: error.message || "Failed to analyze opportunity",
        variant: "destructive",
      })
    } finally {
      setLoadingAnalysis(false)
    }
  }

  // Opportunity Scoring
  const handleScoreOpportunity = async () => {
    if (!selectedOpportunityObj) {
      toast({
        title: "Error",
        description: "Please select an opportunity to score",
        variant: "destructive",
      })
      return
    }

    setLoadingAnalysis(true)
    try {
      const result = await apiClient.scoreOpportunity(selectedOpportunityObj, userProfile)
      setScoringResult(result)
      toast({
        title: "Scoring Complete",
        description: "AI opportunity scoring generated successfully",
      })
    } catch (error) {
      console.error('Scoring failed:', error)
      toast({
        title: "Scoring Failed",
        description: error.message || "Failed to score opportunity",
        variant: "destructive",
      })
    } finally {
      setLoadingAnalysis(false)
    }
  }

  // Competitive Analysis
  const handleCompetitiveAnalysis = async () => {
    if (!naicsCodes.trim() || !agency.trim()) {
      toast({
        title: "Error",
        description: "Please enter NAICS codes and agency",
        variant: "destructive",
      })
      return
    }

    setLoadingCompetitive(true)
    try {
      const codes = naicsCodes.split(',').map(code => code.trim())
      const result = await apiClient.analyzeCompetitiveLandscape(codes, agency, timeframe)
      setCompetitiveResult(result)
      toast({
        title: "Analysis Complete",
        description: "Competitive landscape analysis generated successfully",
      })
    } catch (error) {
      console.error('Competitive analysis failed:', error)
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to analyze competitive landscape",
        variant: "destructive",
      })
    } finally {
      setLoadingCompetitive(false)
    }
  }

  // Smart Alerts
  const handleGenerateAlerts = async () => {
    setLoadingAlerts(true)
    try {
      const result = await apiClient.generateSmartAlerts(userProfile)
      setAlertsResult(result)
      toast({
        title: "Alerts Generated",
        description: "Smart alerts generated successfully",
      })
    } catch (error) {
      console.error('Alerts generation failed:', error)
      toast({
        title: "Alerts Failed",
        description: error.message || "Failed to generate smart alerts",
        variant: "destructive",
      })
    } finally {
      setLoadingAlerts(false)
    }
  }

  // Market Forecasting
  const handleMarketForecast = async () => {
    setLoadingForecast(true)
    try {
      const result = await apiClient.forecastMarketConditions(forecastHorizon)
      setForecastResult(result)
      toast({
        title: "Forecast Generated",
        description: "Market forecast generated successfully",
      })
    } catch (error) {
      console.error('Forecast failed:', error)
      toast({
        title: "Forecast Failed",
        description: error.message || "Failed to generate market forecast",
        variant: "destructive",
      })
    } finally {
      setLoadingForecast(false)
    }
  }

  // Compliance Analysis
  const handleComplianceAnalysis = async () => {
    if (!complianceOpportunity.trim()) {
      toast({
        title: "Error",
        description: "Please enter opportunity details",
        variant: "destructive",
      })
      return
    }

    setLoadingCompliance(true)
    try {
      const opportunity = JSON.parse(complianceOpportunity)
      const result = await apiClient.analyzeCompliance(opportunity)
      setComplianceResult(result)
      toast({
        title: "Analysis Complete",
        description: "Compliance analysis generated successfully",
      })
    } catch (error) {
      console.error('Compliance analysis failed:', error)
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to analyze compliance requirements",
        variant: "destructive",
      })
    } finally {
      setLoadingCompliance(false)
    }
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          🧠 AI Market Intelligence
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Advanced market intelligence and analysis powered by Perplexity AI
        </p>
      </div>

      <Tabs defaultValue="search" className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="search">Market Intelligence</TabsTrigger>
          <TabsTrigger value="opportunity">Opportunity Analysis</TabsTrigger>
          <TabsTrigger value="competitive">Competitive Analysis</TabsTrigger>
          <TabsTrigger value="alerts">Smart Alerts</TabsTrigger>
          <TabsTrigger value="forecast">Market Forecasting</TabsTrigger>
          <TabsTrigger value="compliance">Compliance Analysis</TabsTrigger>
        </TabsList>

        {/* Market Intelligence Search Tab */}
        <TabsContent value="search" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-blue-500" />
                Market Intelligence Search
              </CardTitle>
              <CardDescription>
                Get AI-powered analysis of government contracting markets, trends, and opportunities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Input
                    placeholder="Enter your market intelligence query (e.g., 'healthcare IT government contracts 2024')"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !loading && handleSearch()}
                  />
                </div>
                <Button 
                  onClick={handleSearch}
                  disabled={loading || !searchQuery.trim()}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Generate Intelligence
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Search Results */}
          {searchResult && (
            <Card>
              <CardHeader>
                <CardTitle>AI Analysis Results</CardTitle>
                <CardDescription>
                  Generated on {new Date(searchResult.timestamp).toLocaleString()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {searchResult.analysis}
                  </div>
                </div>
                <div className="mt-4 text-xs text-gray-500">
                  Model: {searchResult.model} | Query: "{searchResult.query}"
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Opportunity Analysis Tab */}
        <TabsContent value="opportunity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                Opportunity Analysis & Scoring
              </CardTitle>
              <CardDescription>
                Enrich opportunity data and get AI-powered scoring based on your profile
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="opportunity-select">Select Real Government RFP</Label>
                    <Button
                      onClick={fetchOpportunities}
                      disabled={loadingOpportunities}
                      size="sm"
                      variant="outline"
                    >
                      {loadingOpportunities ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <RefreshCw className="w-3 h-3" />
                      )}
                    </Button>
                  </div>
                  
                  <div className="space-y-2">
                    <Input
                      placeholder="Search opportunities by title, agency, or description..."
                      value={opportunitySearch}
                      onChange={(e) => setOpportunitySearch(e.target.value)}
                    />
                    
                    <Select value={selectedOpportunityId} onValueChange={handleOpportunitySelect}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={loadingOpportunities ? "Loading opportunities..." : "Select an opportunity to analyze"} />
                      </SelectTrigger>
                      <SelectContent>
                        {opportunities.map((opp) => (
                          <SelectItem key={opp.id} value={opp.id.toString()}>
                            <div className="text-left">
                              <div className="font-medium truncate max-w-96">
                                {opp.title}
                              </div>
                              <div className="text-xs text-gray-500">
                                {opp.agency_name} • ${(opp.estimated_value || 0).toLocaleString()}
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {selectedOpportunityObj && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <h4 className="font-medium text-sm mb-2">Selected Opportunity Preview:</h4>
                      <div className="text-xs space-y-1">
                        <div><strong>Title:</strong> {selectedOpportunityObj.title}</div>
                        <div><strong>Agency:</strong> {selectedOpportunityObj.agency_name}</div>
                        <div><strong>Value:</strong> ${(selectedOpportunityObj.estimated_value || 0).toLocaleString()}</div>
                        <div><strong>Posted:</strong> {new Date(selectedOpportunityObj.posted_date).toLocaleDateString()}</div>
                        {selectedOpportunityObj.due_date && (
                          <div><strong>Due:</strong> {new Date(selectedOpportunityObj.due_date).toLocaleDateString()}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="industry">Your Industry</Label>
                    <Input
                      id="industry"
                      placeholder="e.g., Technology, Healthcare"
                      value={userProfile.industry}
                      onChange={(e) => setUserProfile({...userProfile, industry: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="company-size">Company Size</Label>
                    <Select value={userProfile.company_size} onValueChange={(value) => setUserProfile({...userProfile, company_size: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select size" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="small">Small (1-50)</SelectItem>
                        <SelectItem value="medium">Medium (51-500)</SelectItem>
                        <SelectItem value="large">Large (500+)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="focus">Focus Area</Label>
                    <Input
                      id="focus"
                      placeholder="e.g., Cybersecurity, Data Analytics"
                      value={userProfile.focus}
                      onChange={(e) => setUserProfile({...userProfile, focus: e.target.value})}
                    />
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button 
                    onClick={handleEnrichOpportunity}
                    disabled={loadingAnalysis || !selectedOpportunityObj}
                    className="flex-1"
                  >
                    {loadingAnalysis ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Enriching...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 mr-2" />
                        Enrich Opportunity
                      </>
                    )}
                  </Button>
                  <Button 
                    onClick={handleScoreOpportunity}
                    disabled={loadingAnalysis || !selectedOpportunityObj}
                    className="flex-1"
                    variant="outline"
                  >
                    {loadingAnalysis ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Scoring...
                      </>
                    ) : (
                      <>
                        <Award className="w-4 h-4 mr-2" />
                        Score Opportunity
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Enrichment Results */}
          {enrichmentResult && (
            <Card>
              <CardHeader>
                <CardTitle>Enrichment Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {enrichmentResult.analysis || enrichmentResult.enrichment}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Scoring Results */}
          {scoringResult && (
            <Card>
              <CardHeader>
                <CardTitle>Opportunity Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {scoringResult.analysis || scoringResult.score}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Competitive Analysis Tab */}
        <TabsContent value="competitive" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-500" />
                Competitive Landscape Analysis
              </CardTitle>
              <CardDescription>
                Analyze market competition, key players, and winning strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="naics-codes">NAICS Codes (comma-separated)</Label>
                  <Input
                    id="naics-codes"
                    placeholder="e.g., 541511, 541512, 541513"
                    value={naicsCodes}
                    onChange={(e) => setNaicsCodes(e.target.value)}
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="agency">Target Agency</Label>
                    <Input
                      id="agency"
                      placeholder="e.g., Department of Defense, GSA"
                      value={agency}
                      onChange={(e) => setAgency(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="timeframe">Analysis Timeframe</Label>
                    <Select value={timeframe} onValueChange={setTimeframe}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1year">Past 1 Year</SelectItem>
                        <SelectItem value="2years">Past 2 Years</SelectItem>
                        <SelectItem value="3years">Past 3 Years</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button 
                  onClick={handleCompetitiveAnalysis}
                  disabled={loadingCompetitive || !naicsCodes.trim() || !agency.trim()}
                  className="w-full"
                >
                  {loadingCompetitive ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Competition...
                    </>
                  ) : (
                    <>
                      <Target className="w-4 h-4 mr-2" />
                      Analyze Competitive Landscape
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Competitive Results */}
          {competitiveResult && (
            <Card>
              <CardHeader>
                <CardTitle>Competitive Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {competitiveResult.analysis}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Smart Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-orange-500" />
                Smart Alerts & Predictions
              </CardTitle>
              <CardDescription>
                Generate intelligent alerts about opportunities matching your profile
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Based on your profile settings above, generate personalized alerts for relevant opportunities.
                </p>

                <Button 
                  onClick={handleGenerateAlerts}
                  disabled={loadingAlerts}
                  className="w-full"
                >
                  {loadingAlerts ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating Alerts...
                    </>
                  ) : (
                    <>
                      <Users className="w-4 h-4 mr-2" />
                      Generate Smart Alerts
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Alerts Results */}
          {alertsResult && (
            <Card>
              <CardHeader>
                <CardTitle>Smart Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {alertsResult.analysis || alertsResult.alerts}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Market Forecasting Tab */}
        <TabsContent value="forecast" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Market Forecasting
              </CardTitle>
              <CardDescription>
                Predict future market conditions and upcoming opportunities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="forecast-horizon">Forecast Horizon</Label>
                  <Select value={forecastHorizon} onValueChange={setForecastHorizon}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3months">Next 3 Months</SelectItem>
                      <SelectItem value="6months">Next 6 Months</SelectItem>
                      <SelectItem value="12months">Next 12 Months</SelectItem>
                      <SelectItem value="24months">Next 24 Months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handleMarketForecast}
                  disabled={loadingForecast}
                  className="w-full"
                >
                  {loadingForecast ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating Forecast...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Generate Market Forecast
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Forecast Results */}
          {forecastResult && (
            <Card>
              <CardHeader>
                <CardTitle>Market Forecast</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {forecastResult.analysis || forecastResult.forecast}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Compliance Analysis Tab */}
        <TabsContent value="compliance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-indigo-500" />
                Compliance Analysis
              </CardTitle>
              <CardDescription>
                Analyze regulatory and compliance requirements for opportunities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="compliance-opportunity">Opportunity Data (JSON format)</Label>
                  <Textarea
                    id="compliance-opportunity"
                    placeholder='{"title": "IT Services Contract", "agency": "GSA", "requirements": "...", "certifications": "..."}'
                    value={complianceOpportunity}
                    onChange={(e) => setComplianceOpportunity(e.target.value)}
                    rows={6}
                  />
                </div>

                <Button 
                  onClick={handleComplianceAnalysis}
                  disabled={loadingCompliance || !complianceOpportunity.trim()}
                  className="w-full"
                >
                  {loadingCompliance ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Compliance...
                    </>
                  ) : (
                    <>
                      <FileText className="w-4 h-4 mr-2" />
                      Analyze Compliance Requirements
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Compliance Results */}
          {complianceResult && (
            <Card>
              <CardHeader>
                <CardTitle>Compliance Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {complianceResult.analysis}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}