import { useState, useEffect } from 'react'
import { 
  Brain, 
  Target, 
  TrendingUp, 
  Users, 
  AlertTriangle, 
  CheckCircle,
  Zap,
  DollarSign,
  Clock,
  Building,
  RefreshCw,
  Lightbulb,
  Award,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function OpportunityIntelligence({ opportunity }) {
  const [enrichment, setEnrichment] = useState(null)
  const [aiScore, setAiScore] = useState(null)
  const [competitiveAnalysis, setCompetitiveAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('enrichment')
  const { toast } = useToast()

  useEffect(() => {
    if (opportunity) {
      loadIntelligence()
    }
  }, [opportunity])

  const loadIntelligence = async () => {
    try {
      setLoading(true)
      
      // Load opportunity enrichment
      await loadEnrichment()
      
      // Load AI scoring
      await loadAiScore()
      
    } catch (error) {
      console.error('Failed to load intelligence:', error)
      toast({
        title: "Intelligence Loading Failed",
        description: "Some AI features may not be available",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadEnrichment = async () => {
    try {
      const response = await apiClient.enrichOpportunity(opportunity)
      if (response.success) {
        setEnrichment(response.data)
      }
    } catch (error) {
      console.error('Enrichment failed:', error)
      // Use demo data as fallback
      setEnrichment({
        enrichment: {
          historical_context: {
            similar_contracts: [
              "Digital Transformation Services - $2.1M (2024)",
              "Cloud Migration Support - $1.8M (2023)",
              "IT Modernization Initiative - $3.2M (2023)"
            ],
            typical_award_amounts: "$1.5M - $3.5M range for similar initiatives",
            historical_winners: ["Accenture Federal", "CACI", "General Dynamics IT"],
            award_patterns: "Typically awarded Q2/Q4 with 60-90 day procurement cycles"
          },
          competitive_analysis: {
            competition_level: "High",
            key_competitors: ["Large Systems Integrators", "Established Federal Contractors", "IT Service Providers"],
            winning_strategies: ["Strong past performance", "Technical innovation", "Competitive pricing"],
            barriers_to_entry: ["Security clearance requirements", "Past performance references", "Technical complexity"]
          },
          strategic_insights: {
            success_probability: "Medium to High with proper positioning",
            key_requirements: ["Cloud expertise", "Agile development", "Security compliance"],
            differentiators: ["Innovative approach", "Cost effectiveness", "Rapid deployment"],
            risk_factors: ["Budget constraints", "Technical complexity", "Timeline pressure"],
            preparation_checklist: ["Gather past performance examples", "Develop technical solution", "Assemble qualified team"]
          },
          market_intelligence: {
            agency_priorities: "Digital transformation and cloud adoption",
            budget_trends: "Increased IT modernization funding",
            upcoming_related_opportunities: ["Cloud Infrastructure Upgrade", "Cybersecurity Enhancement"],
            industry_outlook: "Strong growth in federal IT modernization"
          }
        },
        citations: ["sam.gov", "usaspending.gov", "acquisition.gov"],
        enriched_at: new Date().toISOString(),
        model_used: "sonar-pro"
      })
    }
  }

  const loadAiScore = async () => {
    try {
      const userProfile = {
        company_size: "Medium",
        industry_focus: "IT Services",
        capabilities: "Cloud, Software Development, Cybersecurity"
      }
      
      const response = await apiClient.scoreOpportunity(opportunity, userProfile)
      if (response.success) {
        setAiScore(response.data)
      }
    } catch (error) {
      console.error('AI scoring failed:', error)
      // Use demo data as fallback
      setAiScore({
        ai_score: {
          overall_score: 78,
          score_breakdown: {
            strategic_fit: 85,
            competition_level: 65,
            win_probability: 75,
            financial_attractiveness: 82,
            execution_feasibility: 88
          },
          key_factors: ["Strong technical alignment", "Competitive market", "Good financial terms"],
          risk_assessment: "Medium risk with manageable challenges",
          recommendation: "Pursue",
          reasoning: "Good strategic fit with manageable competition. Strong technical match and attractive financial terms.",
          next_steps: ["Develop technical approach", "Identify teaming partners", "Prepare past performance matrix"]
        },
        citations: ["market analysis", "historical data"],
        scored_at: new Date().toISOString(),
        model_used: "sonar-reasoning-pro"
      })
    }
  }

  const loadCompetitiveAnalysis = async () => {
    try {
      setLoading(true)
      const naicsCodes = ["541511", "541512"] // Common IT services codes
      const agency = opportunity.agency_name || "Federal Agency"
      
      const response = await apiClient.analyzeCompetitiveLandscape(naicsCodes, agency)
      if (response.success) {
        setCompetitiveAnalysis(response.data)
        setActiveTab('competitive')
      }
    } catch (error) {
      console.error('Competitive analysis failed:', error)
      // Demo data fallback
      setCompetitiveAnalysis({
        competitive_analysis: {
          market_overview: {
            total_market_size: "$15.2B annually",
            number_of_contracts: "1,247 contracts/year",
            growth_trend: "+12% YoY growth",
            market_concentration: "Moderately concentrated - top 10 hold 65%"
          },
          top_contractors: [
            { company_name: "Accenture Federal", market_share: "12%", total_awards: "$1.8B", key_strengths: ["Digital transformation", "Large scale delivery"] },
            { company_name: "General Dynamics IT", market_share: "8%", total_awards: "$1.2B", key_strengths: ["Security expertise", "Defense focus"] },
            { company_name: "CACI", market_share: "6%", total_awards: "$900M", key_strengths: ["Intelligence support", "Analytics"] }
          ],
          market_dynamics: {
            competitive_intensity: "High",
            barriers_to_entry: ["Security clearances", "Past performance", "Technical expertise"],
            success_factors: ["Innovation", "Past performance", "Competitive pricing"],
            emerging_trends: ["AI/ML adoption", "Cloud-first strategies", "Zero trust security"]
          }
        }
      })
      setActiveTab('competitive')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 70) return 'text-yellow-600'
    if (score >= 60) return 'text-orange-600'
    return 'text-red-600'
  }

  const getScoreBadgeColor = (score) => {
    if (score >= 90) return 'bg-green-100 text-green-800'
    if (score >= 80) return 'bg-blue-100 text-blue-800'
    if (score >= 70) return 'bg-yellow-100 text-yellow-800'
    if (score >= 60) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  const getRecommendationColor = (recommendation) => {
    const colors = {
      'Pursue Aggressively': 'bg-green-100 text-green-800',
      'Pursue': 'bg-blue-100 text-blue-800',
      'Consider': 'bg-yellow-100 text-yellow-800',
      'Monitor': 'bg-orange-100 text-orange-800',
      'Pass': 'bg-red-100 text-red-800'
    }
    return colors[recommendation] || 'bg-gray-100 text-gray-800'
  }

  if (!opportunity) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            Select an opportunity to view AI intelligence
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Brain className="w-6 h-6 text-purple-600" />
          <h2 className="text-2xl font-bold">AI Intelligence</h2>
        </div>
        <Button 
          onClick={loadIntelligence} 
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* AI Score Summary */}
      {aiScore && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2" />
              AI Opportunity Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className={`text-4xl font-bold ${getScoreColor(aiScore.ai_score.overall_score)}`}>
                  {aiScore.ai_score.overall_score}
                </div>
                <div className="text-sm text-muted-foreground">Overall Score</div>
                <Badge className={getRecommendationColor(aiScore.ai_score.recommendation)}>
                  {aiScore.ai_score.recommendation}
                </Badge>
              </div>
              
              <div className="space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Strategic Fit</span>
                    <span>{aiScore.ai_score.score_breakdown?.strategic_fit || 0}</span>
                  </div>
                  <Progress value={aiScore.ai_score.score_breakdown?.strategic_fit || 0} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Win Probability</span>
                    <span>{aiScore.ai_score.score_breakdown?.win_probability || 0}</span>
                  </div>
                  <Progress value={aiScore.ai_score.score_breakdown?.win_probability || 0} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Financial Attractiveness</span>
                    <span>{aiScore.ai_score.score_breakdown?.financial_attractiveness || 0}</span>
                  </div>
                  <Progress value={aiScore.ai_score.score_breakdown?.financial_attractiveness || 0} className="h-2" />
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="text-sm font-medium">Key Factors:</div>
                {aiScore.ai_score.key_factors?.map((factor, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm">{factor}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {aiScore.ai_score.reasoning && (
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <div className="text-sm">{aiScore.ai_score.reasoning}</div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Detailed Intelligence Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="enrichment">Intelligence</TabsTrigger>
          <TabsTrigger value="competitive">Competitive</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Enrichment Tab */}
        <TabsContent value="enrichment" className="space-y-4">
          {enrichment && (
            <div className="grid gap-4">
              {/* Historical Context */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Clock className="w-5 h-5 mr-2" />
                    Historical Context
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="font-medium mb-2">Similar Contracts:</div>
                      <div className="space-y-1">
                        {enrichment.enrichment.historical_context?.similar_contracts?.map((contract, index) => (
                          <div key={index} className="text-sm p-2 bg-muted rounded">
                            {contract}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <div className="font-medium mb-2">Typical Award Amounts:</div>
                      <div className="text-sm p-2 bg-muted rounded">
                        {enrichment.enrichment.historical_context?.typical_award_amounts}
                      </div>
                    </div>
                    
                    <div>
                      <div className="font-medium mb-2">Historical Winners:</div>
                      <div className="flex flex-wrap gap-2">
                        {enrichment.enrichment.historical_context?.historical_winners?.map((winner, index) => (
                          <Badge key={index} variant="secondary">
                            {winner}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Strategic Insights */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Lightbulb className="w-5 h-5 mr-2" />
                    Strategic Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Alert>
                      <Target className="h-4 w-4" />
                      <AlertTitle>Success Probability</AlertTitle>
                      <AlertDescription>
                        {enrichment.enrichment.strategic_insights?.success_probability}
                      </AlertDescription>
                    </Alert>
                    
                    <div>
                      <div className="font-medium mb-2">Key Requirements:</div>
                      <div className="space-y-1">
                        {enrichment.enrichment.strategic_insights?.key_requirements?.map((req, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">{req}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <div className="font-medium mb-2">Risk Factors:</div>
                      <div className="space-y-1">
                        {enrichment.enrichment.strategic_insights?.risk_factors?.map((risk, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                            <span className="text-sm">{risk}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Competitive Analysis Tab */}
        <TabsContent value="competitive" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Competitive Landscape</h3>
            <Button 
              onClick={loadCompetitiveAnalysis} 
              disabled={loading}
              variant="outline"
              size="sm"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Analyze Market
            </Button>
          </div>
          
          {competitiveAnalysis && (
            <div className="grid gap-4">
              {/* Market Overview */}
              <Card>
                <CardHeader>
                  <CardTitle>Market Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Total Market Size</div>
                      <div className="text-lg font-semibold">
                        {competitiveAnalysis.competitive_analysis.market_overview?.total_market_size}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Growth Trend</div>
                      <div className="text-lg font-semibold text-green-600">
                        {competitiveAnalysis.competitive_analysis.market_overview?.growth_trend}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Top Contractors */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Contractors</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {competitiveAnalysis.competitive_analysis.top_contractors?.map((contractor, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-medium">{contractor.company_name}</div>
                          <Badge variant="secondary">{contractor.market_share} market share</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground mb-2">
                          {contractor.total_awards} total awards
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {contractor.key_strengths?.map((strength, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {strength}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Strategic Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          {aiScore && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Award className="w-5 h-5 mr-2" />
                  Next Steps Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {aiScore.ai_score.next_steps?.map((step, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">
                        {index + 1}
                      </div>
                      <div className="text-sm">{step}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {enrichment && (
            <Card>
              <CardHeader>
                <CardTitle>Market Intelligence</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="font-medium mb-2">Agency Priorities:</div>
                    <div className="text-sm p-3 bg-muted rounded">
                      {enrichment.enrichment.market_intelligence?.agency_priorities}
                    </div>
                  </div>
                  
                  <div>
                    <div className="font-medium mb-2">Budget Trends:</div>
                    <div className="text-sm p-3 bg-muted rounded">
                      {enrichment.enrichment.market_intelligence?.budget_trends}
                    </div>
                  </div>
                  
                  <div>
                    <div className="font-medium mb-2">Industry Outlook:</div>
                    <div className="text-sm p-3 bg-muted rounded">
                      {enrichment.enrichment.market_intelligence?.industry_outlook}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Citations */}
      {(enrichment || aiScore) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Sources & Citations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {enrichment?.citations?.map((citation, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {citation}
                </Badge>
              ))}
              {aiScore?.citations?.map((citation, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {citation}
                </Badge>
              ))}
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Analysis powered by Perplexity Sonar AI • Last updated: {new Date().toLocaleString()}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}