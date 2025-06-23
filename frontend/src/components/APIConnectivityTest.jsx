import { useState, useEffect } from 'react'
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { useToast } from '../hooks/use-toast'

const APIConnectivityTest = () => {
  const [testResults, setTestResults] = useState({})
  const [testing, setTesting] = useState(false)
  const [lastTest, setLastTest] = useState(null)
  const { toast } = useToast()

  // API endpoints to test
  const apiEndpoints = [
    {
      name: 'Backend Health',
      url: 'http://localhost:5002/api/health',
      critical: true,
      description: 'Main backend server health check'
    },
    {
      name: 'Fast-Fail API',
      url: 'http://localhost:5002/api/fast-fail/health',
      critical: false,
      description: 'Fast-fail filtering intelligence system'
    },
    {
      name: 'Win Probability API',
      url: 'http://localhost:5002/api/win-probability/health',
      critical: false,
      description: 'ML-powered win probability predictions'
    },
    {
      name: 'Compliance API',
      url: 'http://localhost:5002/api/compliance/health',
      critical: false,
      description: 'Requirements compliance assessment'
    },
    {
      name: 'Trend Analysis API',
      url: 'http://localhost:5002/api/trends/health',
      critical: false,
      description: 'Market trends and anomaly detection'
    },
    {
      name: 'Cost Tracking API',
      url: 'http://localhost:5002/api/costs/health',
      critical: false,
      description: 'API usage cost monitoring'
    },
    {
      name: 'Opportunities API',
      url: 'http://localhost:5002/api/opportunities-debug',
      critical: true,
      description: 'Opportunity data access'
    }
  ]

  useEffect(() => {
    // Run connectivity test on mount
    runConnectivityTest()
  }, [])

  const testEndpoint = async (endpoint) => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout

      const response = await fetch(endpoint.url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      const isJson = response.headers.get('content-type')?.includes('application/json')
      let responseData = null
      
      if (isJson) {
        try {
          responseData = await response.json()
        } catch (e) {
          responseData = { error: 'Invalid JSON response' }
        }
      } else {
        responseData = { text: await response.text() }
      }

      return {
        name: endpoint.name,
        status: response.ok ? 'healthy' : 'error',
        statusCode: response.status,
        responseTime: Date.now(),
        data: responseData,
        critical: endpoint.critical,
        description: endpoint.description,
        error: response.ok ? null : `HTTP ${response.status}: ${response.statusText}`
      }
    } catch (error) {
      return {
        name: endpoint.name,
        status: 'offline',
        statusCode: 0,
        responseTime: Date.now(),
        data: null,
        critical: endpoint.critical,
        description: endpoint.description,
        error: error.name === 'AbortError' ? 'Request timeout' : error.message
      }
    }
  }

  const runConnectivityTest = async () => {
    setTesting(true)
    setLastTest(new Date())
    
    toast({
      title: "Testing API Connectivity",
      description: "Checking all backend services...",
    })

    try {
      const startTime = Date.now()
      
      // Test all endpoints in parallel
      const results = await Promise.all(
        apiEndpoints.map(endpoint => testEndpoint(endpoint))
      )

      // Calculate response times
      const endTime = Date.now()
      const totalTime = endTime - startTime

      // Organize results by name
      const resultMap = {}
      results.forEach(result => {
        result.responseTime = endTime - result.responseTime
        resultMap[result.name] = result
      })

      setTestResults(resultMap)

      // Count successful connections
      const successful = results.filter(r => r.status === 'healthy').length
      const critical = results.filter(r => r.critical && r.status !== 'healthy').length

      if (critical > 0) {
        toast({
          title: "Critical Services Down",
          description: `${critical} critical services are not responding`,
          variant: "destructive",
        })
      } else if (successful === results.length) {
        toast({
          title: "All Services Connected",
          description: `All ${successful} services are healthy`,
        })
      } else {
        toast({
          title: "Partial Connectivity",
          description: `${successful}/${results.length} services are healthy`,
          variant: "secondary",
        })
      }

    } catch (error) {
      console.error('Connectivity test failed:', error)
      toast({
        title: "Connectivity Test Failed",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setTesting(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'offline':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <WifiOff className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusBadge = (status, critical) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-500">Connected</Badge>
      case 'error':
        return <Badge variant="secondary">Error</Badge>
      case 'offline':
        return <Badge variant={critical ? "destructive" : "outline"}>Offline</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const calculateOverallHealth = () => {
    const results = Object.values(testResults)
    if (results.length === 0) return 0
    
    const criticalServices = results.filter(r => r.critical)
    const healthyCritical = criticalServices.filter(r => r.status === 'healthy').length
    const totalCritical = criticalServices.length
    
    if (totalCritical === 0) return 100 // No critical services defined
    
    return Math.round((healthyCritical / totalCritical) * 100)
  }

  const overallHealth = calculateOverallHealth()
  const results = Object.values(testResults)
  const healthyCount = results.filter(r => r.status === 'healthy').length
  const criticalIssues = results.filter(r => r.critical && r.status !== 'healthy').length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center">
            <Wifi className="h-6 w-6 mr-2 text-blue-500" />
            API Connectivity Test
          </h2>
          <p className="text-muted-foreground">
            Monitor backend service health and connectivity
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {lastTest && (
            <span className="text-xs text-muted-foreground">
              Last tested: {lastTest.toLocaleTimeString()}
            </span>
          )}
          <Button onClick={runConnectivityTest} disabled={testing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${testing ? 'animate-spin' : ''}`} />
            {testing ? 'Testing...' : 'Test Connectivity'}
          </Button>
        </div>
      </div>

      {/* Overall Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Overall System Health</span>
            <Badge variant={overallHealth >= 100 ? 'default' : overallHealth >= 50 ? 'secondary' : 'destructive'}>
              {overallHealth}%
            </Badge>
          </CardTitle>
          <CardDescription>
            Critical services connectivity status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={overallHealth} className="mb-4" />
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">{healthyCount}</div>
              <div className="text-xs text-muted-foreground">Healthy Services</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{criticalIssues}</div>
              <div className="text-xs text-muted-foreground">Critical Issues</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{results.length}</div>
              <div className="text-xs text-muted-foreground">Total Services</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Status Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {apiEndpoints.map((endpoint) => {
          const result = testResults[endpoint.name]
          return (
            <Card key={endpoint.name}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(result?.status)}
                    <CardTitle className="text-sm">{endpoint.name}</CardTitle>
                  </div>
                  {getStatusBadge(result?.status, endpoint.critical)}
                </div>
                <CardDescription className="text-xs">
                  {endpoint.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2 text-xs">
                  {result && (
                    <>
                      <div className="flex justify-between">
                        <span>Status Code:</span>
                        <span className={result.statusCode === 200 ? 'text-green-600' : 'text-red-600'}>
                          {result.statusCode || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Response Time:</span>
                        <span>{result.responseTime ? `${result.responseTime}ms` : 'N/A'}</span>
                      </div>
                      {result.error && (
                        <div className="text-red-600 text-xs mt-2 p-2 bg-red-50 rounded">
                          {result.error}
                        </div>
                      )}
                      {result.data && result.status === 'healthy' && (
                        <div className="text-green-600 text-xs mt-2 p-2 bg-green-50 rounded">
                          Service responding normally
                        </div>
                      )}
                    </>
                  )}
                  {!result && !testing && (
                    <div className="text-gray-500">Not tested yet</div>
                  )}
                  {testing && (
                    <div className="text-blue-600">Testing...</div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Debug Information */}
      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Connection Details</CardTitle>
            <CardDescription>Detailed connectivity test results</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {results.map((result) => (
                <div key={result.name} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(result.status)}
                    <div>
                      <p className="text-sm font-medium">{result.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {result.status === 'healthy' ? 'Connected successfully' : result.error}
                      </p>
                    </div>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    {result.responseTime && `${result.responseTime}ms`}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default APIConnectivityTest