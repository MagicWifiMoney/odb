import { useState, useEffect } from 'react'
import { 
  Bell, 
  AlertTriangle, 
  Clock, 
  TrendingUp, 
  Target, 
  Building,
  DollarSign,
  Users,
  Calendar,
  Star,
  RefreshCw,
  CheckCircle,
  ArrowRight,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function SmartAlerts({ userProfile }) {
  const [alerts, setAlerts] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('priority')
  const { toast } = useToast()

  useEffect(() => {
    loadSmartAlerts()
  }, [userProfile])

  const loadSmartAlerts = async () => {
    try {
      setLoading(true)
      
      const response = await apiClient.generateSmartAlerts(userProfile)
      
      if (response.success) {
        setAlerts(response.data)
        toast({
          title: "Smart Alerts Updated",
          description: "Latest opportunity intelligence loaded",
        })
      } else {
        // Use demo data as fallback
        setAlerts({
          smart_alerts: {
            user_profile: userProfile,
            alert_content: "Demo smart alerts content",
            high_priority_count: 3,
            strategic_count: 5,
            intelligence_updates: 2,
            action_items: [
              "Review upcoming Department of Defense IT modernization RFP",
              "Prepare past performance documentation for cloud services",
              "Register for DHS virtual industry day next week",
              "Update SAM.gov certifications before quarterly deadline"
            ]
          },
          high_priority_alerts: [
            {
              id: 1,
              title: "DHS Cybersecurity Enhancement RFP",
              agency: "Department of Homeland Security",
              value: "$50M",
              deadline: "2025-01-15",
              urgency: "high",
              match_score: 95,
              reason: "Perfect match for your cybersecurity and cloud capabilities",
              action: "Industry day scheduled for next Tuesday"
            },
            {
              id: 2,
              title: "Treasury Cloud Migration Services",
              agency: "Department of Treasury",
              value: "$25M",
              deadline: "2025-01-20",
              urgency: "high",
              match_score: 88,
              reason: "Requires AWS certifications and federal experience",
              action: "Q&A period ends this Friday"
            },
            {
              id: 3,
              title: "VA Digital Transformation Initiative",
              agency: "Veterans Affairs",
              value: "$75M",
              deadline: "2025-02-01",
              urgency: "medium",
              match_score: 82,
              reason: "Large-scale opportunity matching your modernization experience",
              action: "Draft RFP released for industry feedback"
            }
          ],
          strategic_opportunities: [
            {
              id: 4,
              title: "DOD Enterprise IT Services OASIS Pool",
              agency: "Department of Defense",
              value: "$15B",
              timeline: "Q2 2025",
              type: "IDIQ",
              match_score: 78,
              description: "Major IT services contract vehicle for next 10 years"
            },
            {
              id: 5,
              title: "GSA Cloud Infrastructure Modernization",
              agency: "General Services Administration",
              value: "$500M",
              timeline: "Q3 2025",
              type: "Multiple Award",
              match_score: 85,
              description: "Government-wide cloud infrastructure modernization initiative"
            },
            {
              id: 6,
              title: "HHS Data Analytics Platform",
              agency: "Health and Human Services",
              value: "$30M",
              timeline: "Q1 2025",
              type: "Single Award",
              match_score: 72,
              description: "Healthcare data analytics and AI platform development"
            }
          ],
          competitive_intelligence: [
            {
              title: "CACI Wins $2.1B Army IT Contract",
              impact: "High",
              relevance: "Competitive landscape shift in defense IT",
              action: "Review CACI's winning strategy for similar opportunities"
            },
            {
              title: "Accenture Federal Protest Resolution",
              impact: "Medium",
              relevance: "Re-compete opportunity may be available",
              action: "Monitor for new solicitation announcement"
            }
          ],
          market_trends: [
            {
              trend: "Zero Trust Architecture Mandate",
              impact: "High",
              description: "All federal agencies required to implement Zero Trust by 2026",
              opportunity: "Increased demand for cybersecurity consulting and implementation"
            },
            {
              trend: "AI/ML Budget Allocation Increase",
              impact: "High", 
              description: "Federal AI budget increased 40% for FY 2025",
              opportunity: "New AI/ML development and deployment opportunities"
            },
            {
              trend: "Small Business Innovation Focus",
              impact: "Medium",
              description: "Enhanced set-aside goals for innovative small businesses",
              opportunity: "Better chances for small business contractors in tech sectors"
            }
          ],
          citations: ["sam.gov", "usaspending.gov", "federalnewsnetwork.com"],
          generated_at: new Date().toISOString()
        })
      }
    } catch (error) {
      console.error('Smart alerts failed:', error)
      toast({
        title: "Alert Update Failed",
        description: "Could not load latest alerts",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case 'high': return 'text-red-600'
      case 'medium': return 'text-orange-600'
      case 'low': return 'text-green-600'
      default: return 'text-gray-600'
    }
  }

  const getUrgencyBadge = (urgency) => {
    switch (urgency) {
      case 'high': return 'destructive'
      case 'medium': return 'default'
      case 'low': return 'secondary'
      default: return 'outline'
    }
  }

  const getMatchScoreColor = (score) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 70) return 'text-orange-600'
    return 'text-gray-600'
  }

  const formatDeadline = (deadline) => {
    const date = new Date(deadline)
    const now = new Date()
    const diffTime = date - now
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays < 0) return 'Overdue'
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Tomorrow'
    if (diffDays <= 7) return `${diffDays} days`
    return `${Math.ceil(diffDays / 7)} weeks`
  }

  if (!alerts) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Loading smart alerts...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bell className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold">Smart Alerts</h2>
        </div>
        <Button 
          onClick={loadSmartAlerts} 
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Updating...' : 'Refresh'}
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div>
                <div className="text-2xl font-bold">{alerts.high_priority_alerts?.length || 0}</div>
                <div className="text-sm text-muted-foreground">High Priority</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-blue-500" />
              <div>
                <div className="text-2xl font-bold">{alerts.strategic_opportunities?.length || 0}</div>
                <div className="text-sm text-muted-foreground">Strategic</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              <div>
                <div className="text-2xl font-bold">{alerts.market_trends?.length || 0}</div>
                <div className="text-sm text-muted-foreground">Market Trends</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-purple-500" />
              <div>
                <div className="text-2xl font-bold">{alerts.smart_alerts?.action_items?.length || 0}</div>
                <div className="text-sm text-muted-foreground">Action Items</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alert Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="priority">High Priority</TabsTrigger>
          <TabsTrigger value="strategic">Strategic</TabsTrigger>
          <TabsTrigger value="intelligence">Intel Updates</TabsTrigger>
          <TabsTrigger value="trends">Market Trends</TabsTrigger>
        </TabsList>

        {/* High Priority Alerts */}
        <TabsContent value="priority" className="space-y-4">
          {alerts.high_priority_alerts?.map((alert) => (
            <Card key={alert.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{alert.title}</CardTitle>
                    <CardDescription className="flex items-center space-x-4 mt-2">
                      <span className="flex items-center">
                        <Building className="w-4 h-4 mr-1" />
                        {alert.agency}
                      </span>
                      <span className="flex items-center">
                        <DollarSign className="w-4 h-4 mr-1" />
                        {alert.value}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {formatDeadline(alert.deadline)}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex space-x-2">
                    <Badge variant={getUrgencyBadge(alert.urgency)}>
                      {alert.urgency.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" className={getMatchScoreColor(alert.match_score)}>
                      {alert.match_score}% Match
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <span className="font-medium">Why this matters: </span>
                    <span className="text-muted-foreground">{alert.reason}</span>
                  </div>
                  <Alert>
                    <Zap className="h-4 w-4" />
                    <AlertTitle>Next Action</AlertTitle>
                    <AlertDescription>{alert.action}</AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Strategic Opportunities */}
        <TabsContent value="strategic" className="space-y-4">
          {alerts.strategic_opportunities?.map((opportunity) => (
            <Card key={opportunity.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{opportunity.title}</CardTitle>
                    <CardDescription className="flex items-center space-x-4 mt-2">
                      <span className="flex items-center">
                        <Building className="w-4 h-4 mr-1" />
                        {opportunity.agency}
                      </span>
                      <span className="flex items-center">
                        <DollarSign className="w-4 h-4 mr-1" />
                        {opportunity.value}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {opportunity.timeline}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex space-x-2">
                    <Badge variant="secondary">{opportunity.type}</Badge>
                    <Badge variant="outline" className={getMatchScoreColor(opportunity.match_score)}>
                      {opportunity.match_score}% Match
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{opportunity.description}</p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Competitive Intelligence */}
        <TabsContent value="intelligence" className="space-y-4">
          {alerts.competitive_intelligence?.map((intel, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium">{intel.title}</h4>
                  <Badge variant={intel.impact === 'High' ? 'destructive' : 'secondary'}>
                    {intel.impact} Impact
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{intel.relevance}</p>
                <div className="flex items-center space-x-2 text-sm">
                  <ArrowRight className="w-4 h-4 text-blue-500" />
                  <span className="font-medium">Action:</span>
                  <span>{intel.action}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Market Trends */}
        <TabsContent value="trends" className="space-y-4">
          {alerts.market_trends?.map((trend, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{trend.trend}</CardTitle>
                  <Badge variant={trend.impact === 'High' ? 'destructive' : 'secondary'}>
                    {trend.impact} Impact
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-muted-foreground">{trend.description}</p>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <Star className="w-4 h-4 text-blue-500 mt-0.5" />
                      <div>
                        <div className="font-medium text-sm">Opportunity</div>
                        <div className="text-sm text-muted-foreground">{trend.opportunity}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {/* Action Items */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            This Week's Action Items
          </CardTitle>
          <CardDescription>
            AI-recommended actions based on your profile and market intelligence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {alerts.smart_alerts?.action_items?.map((item, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-muted/50">
                <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium mt-0.5">
                  {index + 1}
                </div>
                <span className="text-sm">{item}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sources */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Intelligence Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {alerts.citations?.map((citation, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {citation}
              </Badge>
            ))}
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            Alerts powered by Perplexity Sonar AI • Last updated: {new Date(alerts.generated_at).toLocaleString()}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}