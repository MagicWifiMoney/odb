import { useState, useEffect } from 'react'
import { 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  TrendingUp,
  Brain
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Alert, AlertDescription } from './ui/alert'
import IntelligenceCard from './IntelligenceCard'
import { fastFailAPI, winProbabilityAPI, complianceAPI, trendAPI, healthCheckAll } from '../services/api'
import { useToast } from '../hooks/use-toast'

const IntelligenceDashboard = () => {
  const [intelligenceData, setIntelligenceData] = useState({
    fastFail: null,
    winProbability: null,
    compliance: null,
    trends: null
  })
  const [loading, setLoading] = useState({
    fastFail: true,
    winProbability: true,
    compliance: true,
    trends: true
  })
  const [serviceHealth, setServiceHealth] = useState([])
  const [lastUpdate, setLastUpdate] = useState(null)
  const { toast } = useToast()

  useEffect(() => {
    loadIntelligenceData()
    checkServiceHealth()
  }, [])

  const loadIntelligenceData = async () => {
    setLoading({
      fastFail: true,
      winProbability: true,
      compliance: true,
      trends: true
    })

    try {
      // Load all intelligence data in parallel
      const [fastFailData, winProbData, complianceData, trendsData] = await Promise.allSettled([
        fastFailAPI.getDashboard(),
        winProbabilityAPI.getDashboard(),
        complianceAPI.getDashboard(),
        trendAPI.getDashboard()
      ])

      // Process Fast-Fail data
      if (fastFailData.status === 'fulfilled') {
        setIntelligenceData(prev => ({ ...prev, fastFail: fastFailData.value }))
      } else {
        console.error('Fast-Fail data failed:', fastFailData.reason)
      }

      // Process Win Probability data
      if (winProbData.status === 'fulfilled') {
        setIntelligenceData(prev => ({ ...prev, winProbability: winProbData.value }))
      } else {
        console.error('Win Probability data failed:', winProbData.reason)
      }

      // Process Compliance data
      if (complianceData.status === 'fulfilled') {
        setIntelligenceData(prev => ({ ...prev, compliance: complianceData.value }))
      } else {
        console.error('Compliance data failed:', complianceData.reason)
      }

      // Process Trends data
      if (trendsData.status === 'fulfilled') {
        setIntelligenceData(prev => ({ ...prev, trends: trendsData.value }))
      } else {
        console.error('Trends data failed:', trendsData.reason)
      }

      setLastUpdate(new Date())

    } catch (error) {
      console.error('Failed to load intelligence data:', error)
      toast({
        title: "Error",
        description: "Failed to load intelligence data",
        variant: "destructive",
      })
    } finally {
      setLoading({
        fastFail: false,
        winProbability: false,
        compliance: false,
        trends: false
      })
    }
  }

  const checkServiceHealth = async () => {
    try {
      const healthResults = await healthCheckAll()
      setServiceHealth(healthResults)
    } catch (error) {
      console.error('Health check failed:', error)
    }
  }

  const refreshIntelligence = async () => {
    toast({
      title: "Refreshing Intelligence",
      description: "Updating all intelligence systems...",
    })
    
    await loadIntelligenceData()
    await checkServiceHealth()
    
    toast({
      title: "Intelligence Updated",
      description: "All intelligence systems have been refreshed",
    })
  }

  const getHealthStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'unhealthy':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <Info className="h-4 w-4 text-yellow-500" />
    }
  }

  const getHealthStatusBadge = (status) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-500">Healthy</Badge>
      case 'unhealthy':
        return <Badge variant="destructive">Unhealthy</Badge>
      default:
        return <Badge variant="secondary">Unknown</Badge>
    }
  }

  const anyLoading = Object.values(loading).some(Boolean)
  const anyUnhealthy = serviceHealth.some(service => service.status === 'unhealthy')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center">
            <Brain className="h-6 w-6 mr-2 text-purple-500" />
            Intelligence Hub
          </h2>
          <p className="text-muted-foreground">
            AI-powered insights and recommendations
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {lastUpdate && (
            <span className="text-xs text-muted-foreground">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <Button onClick={refreshIntelligence} disabled={anyLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${anyLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Service Health Alert */}
      {anyUnhealthy && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Some intelligence services are experiencing issues. Check service status below.
          </AlertDescription>
        </Alert>
      )}

      {/* Intelligence Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <IntelligenceCard
          type="fast-fail"
          data={intelligenceData.fastFail}
          loading={loading.fastFail}
          onRefresh={() => loadIntelligenceData()}
        />
        <IntelligenceCard
          type="win-probability"
          data={intelligenceData.winProbability}
          loading={loading.winProbability}
          onRefresh={() => loadIntelligenceData()}
        />
        <IntelligenceCard
          type="compliance"
          data={intelligenceData.compliance}
          loading={loading.compliance}
          onRefresh={() => loadIntelligenceData()}
        />
        <IntelligenceCard
          type="trends"
          data={intelligenceData.trends}
          loading={loading.trends}
          onRefresh={() => loadIntelligenceData()}
        />
      </div>

      {/* Service Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Service Health</CardTitle>
          <CardDescription>Status of intelligence backend services</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            {serviceHealth.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-2">
                  {getHealthStatusIcon(service.status)}
                  <span className="text-sm font-medium capitalize">
                    {service.name.replace('-', ' ')}
                  </span>
                </div>
                {getHealthStatusBadge(service.status)}
              </div>
            ))}
          </div>
          {serviceHealth.length === 0 && (
            <div className="text-center py-4 text-muted-foreground">
              <Info className="h-8 w-8 mx-auto mb-2" />
              <p>Service health check in progress...</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Intelligence Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Intelligence Summary</CardTitle>
          <CardDescription>Key insights from all intelligence systems</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Fast-Fail Summary */}
            {intelligenceData.fastFail && (
              <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800">
                <div>
                  <p className="font-medium text-red-800 dark:text-red-200">
                    Fast-Fail Filtering
                  </p>
                  <p className="text-sm text-red-600 dark:text-red-300">
                    {intelligenceData.fastFail.excluded_count || 0} opportunities excluded, 
                    saving {intelligenceData.fastFail.time_saved_hours || 0} hours
                  </p>
                </div>
                <TrendingUp className="h-5 w-5 text-red-500" />
              </div>
            )}

            {/* Win Probability Summary */}
            {intelligenceData.winProbability && (
              <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800">
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-200">
                    Win Probability Analysis
                  </p>
                  <p className="text-sm text-blue-600 dark:text-blue-300">
                    {intelligenceData.winProbability.high_probability_count || 0} high-probability opportunities identified
                  </p>
                </div>
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
            )}

            {/* Compliance Summary */}
            {intelligenceData.compliance && (
              <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800">
                <div>
                  <p className="font-medium text-green-800 dark:text-green-200">
                    Compliance Assessment
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-300">
                    {intelligenceData.compliance.ready_opportunities_count || 0} opportunities ready for pursuit
                  </p>
                </div>
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
            )}

            {/* Trends Summary */}
            {intelligenceData.trends && (
              <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-200 dark:border-purple-800">
                <div>
                  <p className="font-medium text-purple-800 dark:text-purple-200">
                    Market Trends
                  </p>
                  <p className="text-sm text-purple-600 dark:text-purple-300">
                    {intelligenceData.trends.anomalies_detected || 0} anomalies detected in market patterns
                  </p>
                </div>
                <TrendingUp className="h-5 w-5 text-purple-500" />
              </div>
            )}

            {!Object.values(intelligenceData).some(Boolean) && !anyLoading && (
              <div className="text-center py-8 text-muted-foreground">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No intelligence data available</p>
                <p className="text-sm">Try refreshing to load the latest insights</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default IntelligenceDashboard