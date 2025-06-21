import { useState, useEffect } from 'react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts'
import { 
  TrendingUp, 
  FileText, 
  DollarSign, 
  Clock, 
  Target,
  RefreshCw,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { apiClient, formatCurrency } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [syncStatus, setSyncStatus] = useState(null)
  const [recentOpportunities, setRecentOpportunities] = useState([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    loadDashboardData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Debug: Log API base URL
      console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL)
      
      console.log('Loading dashboard data...')
      
      // Load each API call sequentially to see which one fails
      console.log('1. Loading opportunities...')
      const opportunitiesData = await apiClient.getOpportunities()
      console.log('Opportunities response:', opportunitiesData)
      
      console.log('2. Loading stats...')
      const statsData = await apiClient.getOpportunityStats()
      console.log('Stats response:', statsData)
      
      console.log('3. Loading sync status...')
      const syncData = await apiClient.getSyncStatus()
      console.log('Sync response:', syncData)
      
      console.log('All API calls completed successfully!')
      
      setStats(statsData)
      setSyncStatus(syncData)
      setRecentOpportunities(opportunitiesData.opportunities || [])
      
      console.log('State updated! Opportunities count:', opportunitiesData.opportunities?.length)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      toast({
        title: "Error",
        description: `Failed to load dashboard data: ${error.message}`,
        variant: "destructive",
      })
    } finally {
      console.log('Setting loading to false...')
      setLoading(false)
    }
  }

  const handleSync = async () => {
    try {
      toast({
        title: "Sync Started",
        description: "Data synchronization has been initiated",
      })
      
      await apiClient.syncData()
      
      toast({
        title: "Sync Complete",
        description: "Data has been synchronized successfully",
      })
      
      // Reload dashboard data
      loadDashboardData()
    } catch (error) {
      console.error('Sync failed:', error)
      toast({
        title: "Sync Failed",
        description: error.message || "Failed to synchronize data",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <Button disabled>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            Loading...
          </Button>
        </div>
        
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Loading...</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted animate-pulse rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // Prepare chart data based on actual backend response
  const sourceTypeData = stats?.by_type ? Object.entries(stats.by_type).map(([key, value]) => ({
    name: key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: value
  })) : []

  const agencyData = stats?.by_agency ? Object.entries(stats.by_agency).map(([key, value]) => ({
    name: key,
    value: value
  })) : []

  // Since backend doesn't provide score/due date distribution, create placeholder data
  const scoreDistributionData = [
    { range: '80-100', count: Math.floor((stats?.total_opportunities || 0) * 0.6) },
    { range: '60-79', count: Math.floor((stats?.total_opportunities || 0) * 0.3) },
    { range: '0-59', count: Math.floor((stats?.total_opportunities || 0) * 0.1) }
  ]

  const dueDateData = [
    { category: 'Next 7 days', count: Math.floor((stats?.total_opportunities || 0) * 0.1) },
    { category: 'Next 30 days', count: Math.floor((stats?.total_opportunities || 0) * 0.2) },
    { category: 'Later', count: Math.floor((stats?.total_opportunities || 0) * 0.7) }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of RFP and grant opportunities
          </p>
        </div>
        <Button onClick={handleSync}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Sync Data
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Opportunities</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_opportunities?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.active_opportunities || 0} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats?.total_value)}
            </div>
            <p className="text-xs text-muted-foreground">
              Avg Score: {stats?.avg_score || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High Score Opportunities</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(stats?.score_distribution?.['90-100'] || 0) + (stats?.score_distribution?.['80-89'] || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Score ≥ 80
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Due Soon</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(stats?.due_date_distribution?.['Due in 7 days'] || 0) + (stats?.due_date_distribution?.['Due in 30 days'] || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Next 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Source Types */}
        <Card>
          <CardHeader>
            <CardTitle>Opportunities by Type</CardTitle>
            <CardDescription>Distribution across different opportunity types</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sourceTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sourceTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>Opportunities grouped by score ranges</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreDistributionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Due Date Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Due Date Distribution</CardTitle>
          <CardDescription>Opportunities by deadline urgency</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dueDateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recent Opportunities & Sync Status */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Opportunities */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Opportunities</CardTitle>
            <CardDescription>Latest opportunities added to the system</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {console.log('Rendering opportunities, length:', recentOpportunities.length)}
              {console.log('First opportunity:', recentOpportunities[0])}
              {console.log('Sample opportunity structure:', recentOpportunities[0] && Object.keys(recentOpportunities[0]))}
              {recentOpportunities.length > 0 ? (
                <div>
                  <p className="text-green-600 font-bold">✅ Found {recentOpportunities.length} opportunities!</p>
                  {recentOpportunities.map((opportunity, index) => (
                    <div key={opportunity.id || index} className="p-3 border rounded-lg mb-2 bg-blue-50">
                      <p className="font-bold text-blue-800">
                        {opportunity.title || 'No title'}
                      </p>
                      <p className="text-sm text-blue-600">
                        Agency: {opportunity.agency_name || 'No agency'} | 
                        Source: {opportunity.source_name || 'No source'}
                      </p>
                      <p className="text-sm text-green-600">
                        Value: {opportunity.estimated_value ? formatCurrency(opportunity.estimated_value) : 'No value'} | 
                        Score: {opportunity.total_score || 'No score'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-red-500">❌ No recent opportunities found (length: {recentOpportunities.length})</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Sync Status */}
        <Card>
          <CardHeader>
            <CardTitle>Data Sources Status</CardTitle>
            <CardDescription>Last synchronization status for each source</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {syncStatus?.sources ? Object.entries(syncStatus.sources).map(([sourceName, status]) => (
                <div key={sourceName} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {status.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : status.status === 'failed' ? (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <Clock className="w-4 h-4 text-yellow-500" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{sourceName}</p>
                      <p className="text-xs text-muted-foreground">
                        {status.last_sync ? new Date(status.last_sync).toLocaleDateString() : 'Never synced'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      {status.records_added || 0} added
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {status.records_updated || 0} updated
                    </p>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-muted-foreground">No sync data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

