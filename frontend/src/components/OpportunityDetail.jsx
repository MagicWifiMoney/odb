import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  ArrowLeft, 
  ExternalLink, 
  Calendar, 
  DollarSign, 
  Building, 
  MapPin, 
  Phone, 
  Mail,
  Target,
  TrendingUp,
  Clock,
  Users,
  FileText
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import { formatCurrency, formatDate, formatRelativeDate, getScoreColor, getScoreBadgeColor, getUrgencyColor, getSourceTypeLabel, getSourceTypeColor } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { supabase } from '@/lib/supabase'

export default function OpportunityDetail() {
  const { id } = useParams()
  const [opportunity, setOpportunity] = useState(null)
  const [scoreExplanation, setScoreExplanation] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadOpportunityDetail()
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  const loadOpportunityDetail = async () => {
    try {
      setLoading(true)
      
      console.log('Loading opportunity detail from Supabase for ID:', id, 'Type:', typeof id)
      
      // Try both string and number ID formats
      const { data: opportunityData, error } = await supabase
        .from('opportunities')
        .select('*')
        .eq('id', id)
        .single()
      
      console.log('Supabase query result:', { data: opportunityData, error })
      
      // If not found with string ID, try converting to number
      if (!opportunityData && !error) {
        console.log('Trying with numeric ID...')
        const numericId = parseInt(id, 10)
        if (!isNaN(numericId)) {
          const { data: numericData, error: numericError } = await supabase
            .from('opportunities')
            .select('*')
            .eq('id', numericId)
            .single()
          
          console.log('Numeric ID query result:', { data: numericData, error: numericError })
          
          if (numericData && !numericError) {
            console.log('Found with numeric ID!')
            setOpportunity(numericData)
            return
          }
        }
      }
      
      if (error) {
        console.error('Supabase error:', error)
        throw new Error(`Failed to load opportunity: ${error.message}`)
      }
      
      if (!opportunityData) {
        throw new Error('Opportunity not found')
      }
      
      console.log('Opportunity loaded successfully:', opportunityData)
      setOpportunity(opportunityData)
      
      // Try to fetch score explanation from backend API (optional)
      try {
        // Use correct backend URL (Cursor agent changed port to 5002)
        const API_BASE_URL = import.meta.env.VITE_API_URL || 
                            (import.meta.env.PROD ? 'https://api.rfptracking.com' : 'http://localhost:5002')
        const response = await fetch(`${API_BASE_URL}/api/opportunities/${id}/score-explanation`)
        if (response.ok) {
          const scoreData = await response.json()
          setScoreExplanation(scoreData)
          console.log('Score explanation loaded from backend API')
        }
      } catch (scoreError) {
        console.warn('Score explanation not available from backend API:', scoreError)
        // This is non-critical, continue without score explanation
        setScoreExplanation(null)
      }
      
    } catch (error) {
      console.error('Failed to load opportunity detail:', error)
      toast({
        title: "Error",
        description: `Failed to load opportunity details: ${error.message}`,
        variant: "destructive",
      })
      setOpportunity(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/opportunities">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Opportunities
            </Link>
          </Button>
        </div>
        
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="h-8 bg-muted animate-pulse rounded"></div>
              <div className="h-4 bg-muted animate-pulse rounded w-3/4"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="h-4 bg-muted animate-pulse rounded"></div>
                <div className="h-4 bg-muted animate-pulse rounded"></div>
                <div className="h-4 bg-muted animate-pulse rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (!opportunity) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/opportunities">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Opportunities
            </Link>
          </Button>
        </div>
        
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Opportunity not found</h3>
            <p className="text-muted-foreground">
              The requested opportunity could not be found.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/opportunities">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Opportunities
          </Link>
        </Button>
        
        {opportunity.source_url && (
          <Button asChild>
            <a href={opportunity.source_url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4 mr-2" />
              View Original
            </a>
          </Button>
        )}
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Title and Basic Info */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-2xl mb-2">{opportunity.title}</CardTitle>
                  <div className="flex items-center space-x-2 mb-4">
                    <Badge className={getScoreBadgeColor(opportunity.total_score)}>
                      <Target className="w-3 h-3 mr-1" />
                      Score: {opportunity.total_score}
                    </Badge>
                    <Badge variant="outline" className={getSourceTypeColor(opportunity.source_type)}>
                      {getSourceTypeLabel(opportunity.source_type)}
                    </Badge>
                    <Badge variant="secondary">
                      {opportunity.source_name}
                    </Badge>
                  </div>
                </div>
              </div>
              
              {opportunity.opportunity_number && (
                <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                  <span className="font-medium">Opportunity Number:</span>
                  <span>{opportunity.opportunity_number}</span>
                </div>
              )}
            </CardHeader>
            
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Description</h4>
                  <p className="text-muted-foreground leading-relaxed">
                    {opportunity.description || 'No description available'}
                  </p>
                </div>
                
                {opportunity.keywords && opportunity.keywords.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Keywords</h4>
                    <div className="flex flex-wrap gap-2">
                      {opportunity.keywords.map((keyword, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Key Details */}
          <Card>
            <CardHeader>
              <CardTitle>Key Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <Building className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="font-medium">Agency</p>
                      <p className="text-muted-foreground">
                        {opportunity.agency_name || 'Not specified'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <DollarSign className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="font-medium">Estimated Value</p>
                      <p className="text-muted-foreground">
                        {opportunity.estimated_value ? formatCurrency(opportunity.estimated_value) : 'Not specified'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <MapPin className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="font-medium">Location</p>
                      <p className="text-muted-foreground">
                        {opportunity.location || 'Not specified'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <Calendar className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="font-medium">Posted Date</p>
                      <p className="text-muted-foreground">
                        {opportunity.posted_date ? formatDate(opportunity.posted_date) : 'Not specified'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <Clock className={`w-5 h-5 mt-0.5 ${getUrgencyColor(opportunity.due_date)}`} />
                    <div>
                      <p className="font-medium">Due Date</p>
                      <p className={getUrgencyColor(opportunity.due_date)}>
                        {opportunity.due_date ? (
                          <>
                            {formatDate(opportunity.due_date)}
                            <span className="block text-sm">
                              ({formatRelativeDate(opportunity.due_date)})
                            </span>
                          </>
                        ) : 'Not specified'}
                      </p>
                    </div>
                  </div>

                  {opportunity.contact_info && (
                    <div className="flex items-start space-x-3">
                      <Mail className="w-5 h-5 text-muted-foreground mt-0.5" />
                      <div>
                        <p className="font-medium">Contact</p>
                        <p className="text-muted-foreground text-sm">
                          {opportunity.contact_info}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Score Breakdown */}
        <div className="space-y-6">
          {/* Overall Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Target className="w-5 h-5 mr-2" />
                Overall Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className={`text-4xl font-bold ${getScoreColor(opportunity.total_score)}`}>
                  {opportunity.total_score}
                </div>
                <p className="text-muted-foreground">out of 100</p>
                <Progress 
                  value={opportunity.total_score} 
                  className="mt-4"
                />
              </div>
            </CardContent>
          </Card>

          {/* Score Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Score Breakdown</CardTitle>
              <CardDescription>
                How this opportunity was scored
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-blue-500" />
                    <span className="text-sm font-medium">Relevance</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{opportunity.relevance_score}</span>
                    <div className="w-16">
                      <Progress value={opportunity.relevance_score} className="h-2" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-orange-500" />
                    <span className="text-sm font-medium">Urgency</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{opportunity.urgency_score}</span>
                    <div className="w-16">
                      <Progress value={opportunity.urgency_score} className="h-2" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <DollarSign className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-medium">Value</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{opportunity.value_score}</span>
                    <div className="w-16">
                      <Progress value={opportunity.value_score} className="h-2" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4 text-purple-500" />
                    <span className="text-sm font-medium">Competition</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{opportunity.competition_score}</span>
                    <div className="w-16">
                      <Progress value={opportunity.competition_score} className="h-2" />
                    </div>
                  </div>
                </div>
              </div>

              {scoreExplanation && (
                <div className="mt-6 pt-4 border-t">
                  <h4 className="font-medium mb-2">Scoring Details</h4>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    {scoreExplanation.explanation && (
                      <p>{scoreExplanation.explanation}</p>
                    )}
                    {scoreExplanation.factors && scoreExplanation.factors.length > 0 && (
                      <ul className="list-disc list-inside space-y-1">
                        {scoreExplanation.factors.map((factor, index) => (
                          <li key={index}>{factor}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Source:</span>
                  <span className="font-medium">{opportunity.source_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="font-medium">{getSourceTypeLabel(opportunity.source_type)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Added:</span>
                  <span className="font-medium">
                    {opportunity.created_at ? formatDate(opportunity.created_at) : 'Unknown'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Updated:</span>
                  <span className="font-medium">
                    {opportunity.updated_at ? formatDate(opportunity.updated_at) : 'Unknown'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

