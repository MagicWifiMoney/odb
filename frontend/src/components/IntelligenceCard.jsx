import { useState, useEffect } from 'react'
import { 
  Shield, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  XCircle,
  Clock,
  Target,
  Brain
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Progress } from './ui/progress'
import { fastFailAPI, winProbabilityAPI, complianceAPI, trendAPI } from '../services/api'
import { useToast } from '../hooks/use-toast'

const IntelligenceCard = ({ type, data, loading, onRefresh }) => {
  const getCardConfig = () => {
    switch (type) {
      case 'fast-fail':
        return {
          title: 'Fast-Fail Recommendations',
          description: 'Automated filtering and exclusion recommendations',
          icon: Shield,
          color: 'text-red-500'
        }
      case 'win-probability':
        return {
          title: 'Win Probability Analysis',
          description: 'ML-powered success predictions',
          icon: Target,
          color: 'text-blue-500'
        }
      case 'compliance':
        return {
          title: 'Compliance Matrix',
          description: 'Requirements and readiness assessment',
          icon: CheckCircle,
          color: 'text-green-500'
        }
      case 'trends':
        return {
          title: 'Trend Analysis',
          description: 'Market trends and anomaly detection',
          icon: TrendingUp,
          color: 'text-purple-500'
        }
      default:
        return {
          title: 'Intelligence',
          description: 'AI-powered insights',
          icon: Brain,
          color: 'text-gray-500'
        }
    }
  }

  const config = getCardConfig()
  const IconComponent = config.icon

  if (loading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium flex items-center">
            <IconComponent className={`h-4 w-4 mr-2 ${config.color}`} />
            {config.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="h-6 bg-muted animate-pulse rounded"></div>
            <div className="h-4 bg-muted animate-pulse rounded w-3/4"></div>
            <div className="h-4 bg-muted animate-pulse rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const renderContent = () => {
    switch (type) {
      case 'fast-fail':
        return (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {data?.excluded_count || 0}
              </span>
              <Badge variant="destructive">
                Excluded
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Flagged for Review:</span>
                <span className="font-medium">{data?.flagged_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Time Saved:</span>
                <span className="font-medium">{data?.time_saved_hours || 0}h</span>
              </div>
            </div>
            {data?.top_exclusion_reasons && (
              <div className="text-xs text-muted-foreground">
                Top reason: {data.top_exclusion_reasons[0]?.reason}
              </div>
            )}
          </div>
        )

      case 'win-probability':
        return (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {data?.average_win_probability ? `${Math.round(data.average_win_probability * 100)}%` : 'N/A'}
              </span>
              <Badge variant={data?.average_win_probability > 0.7 ? 'default' : data?.average_win_probability > 0.4 ? 'secondary' : 'outline'}>
                Avg Win Rate
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>High Probability (&gt;70%):</span>
                <span className="font-medium">{data?.high_probability_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Medium Probability:</span>
                <span className="font-medium">{data?.medium_probability_count || 0}</span>
              </div>
            </div>
            {data?.confidence_score && (
              <Progress value={data.confidence_score * 100} className="h-2" />
            )}
          </div>
        )

      case 'compliance':
        return (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {data?.overall_readiness_score ? `${Math.round(data.overall_readiness_score * 100)}%` : 'N/A'}
              </span>
              <Badge variant={data?.overall_readiness_score > 0.8 ? 'default' : data?.overall_readiness_score > 0.6 ? 'secondary' : 'destructive'}>
                Readiness
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Critical Gaps:</span>
                <span className="font-medium text-red-500">{data?.critical_gaps_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Ready Opportunities:</span>
                <span className="font-medium text-green-500">{data?.ready_opportunities_count || 0}</span>
              </div>
            </div>
            {data?.top_gap_categories && (
              <div className="text-xs text-muted-foreground">
                Top gap: {data.top_gap_categories[0]?.category}
              </div>
            )}
          </div>
        )

      case 'trends':
        return (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {data?.anomalies_detected || 0}
              </span>
              <Badge variant={data?.anomalies_detected > 0 ? 'destructive' : 'default'}>
                Anomalies
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Trending Up:</span>
                <span className="font-medium text-green-500">{data?.trending_up_count || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Trending Down:</span>
                <span className="font-medium text-red-500">{data?.trending_down_count || 0}</span>
              </div>
            </div>
            {data?.latest_trend && (
              <div className="text-xs text-muted-foreground">
                Latest: {data.latest_trend.category} ({data.latest_trend.direction})
              </div>
            )}
          </div>
        )

      default:
        return (
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground">
              No data available
            </div>
          </div>
        )
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center">
          <IconComponent className={`h-4 w-4 mr-2 ${config.color}`} />
          {config.title}
        </CardTitle>
        {onRefresh && (
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <Clock className="h-3 w-3" />
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {renderContent()}
      </CardContent>
    </Card>
  )
}

export default IntelligenceCard