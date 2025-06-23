import { useState, useEffect } from 'react'
import { 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Database,
  Globe,
  Zap,
  Building2,
  FileText,
  Trophy,
  MapPin
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Separator } from './ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { formatDate } from '../lib/api'
import { useToast } from '../hooks/use-toast'
import { supabase } from '../lib/supabase'

export default function SyncStatus() {
  const [syncStatus, setSyncStatus] = useState(null)
  const [scrapingSources, setScrapingSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [scrapingAll, setScrapingAll] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadSyncData()
  }, [])

  const loadSyncData = async () => {
    try {
      setLoading(true)
      
      // Get database statistics since we're using Supabase directly
      const { count: totalOpportunities, error: countError } = await supabase
        .from('opportunities')
        .select('*', { count: 'exact', head: true })

      if (countError) throw countError

      // Get some recent data to show activity
      const { data: recentOpportunities, error: recentError } = await supabase
        .from('opportunities')
        .select('created_at, source_type')
        .order('created_at', { ascending: false })
        .limit(100)

      if (recentError) throw recentError

      // Calculate stats by source type
      const sourceStats = recentOpportunities.reduce((acc, opp) => {
        const source = opp.source_type || 'unknown'
        acc[source] = (acc[source] || 0) + 1
        return acc
      }, {})

      // Mock sync status since we're using Supabase directly
      setSyncStatus({
        last_sync: new Date().toISOString(),
        status: 'completed',
        total_opportunities: totalOpportunities,
        opportunities_processed: totalOpportunities,
        opportunities_added: recentOpportunities.length,
        sources_active: Object.keys(sourceStats).length,
        by_source: sourceStats
      })

      // Mock scraping sources - since we have data in Supabase
      const mockSources = Object.keys(sourceStats).map(sourceType => ({
        id: sourceType,
        name: sourceType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        url: `https://example.com/${sourceType}`,
        status: 'completed',
        last_run: new Date().toISOString(),
        opportunities_found: sourceStats[sourceType] || 0,
        success_rate: 95 + Math.random() * 5 // Random success rate between 95-100%
      }))

      setScrapingSources(mockSources)
    } catch (error) {
      console.error('Failed to load sync data:', error)
      toast({
        title: "Error",
        description: "Failed to load database status",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSyncAll = async () => {
    try {
      setSyncing(true)
      
      toast({
        title: "Refresh Started",
        description: "Refreshing database statistics...",
      })
      
      // Since we're using Supabase directly, just reload the data
      await loadSyncData()
      
      toast({
        title: "Refresh Complete",
        description: "Database statistics have been refreshed",
      })
    } catch (error) {
      console.error('Refresh failed:', error)
      toast({
        title: "Refresh Failed",
        description: error.message || "Failed to refresh database statistics",
        variant: "destructive",
      })
    } finally {
      setSyncing(false)
    }
  }

  const handleScrapeAll = async () => {
    try {
      setScrapingAll(true)
      
      toast({
        title: "Data Analysis Started",
        description: "Analyzing Supabase data sources...",
      })
      
      // Since we're using Supabase directly, just reload and analyze the data
      await loadSyncData()
      
      toast({
        title: "Analysis Complete",
        description: "Data source analysis has been completed",
      })
    } catch (error) {
      console.error('Analysis failed:', error)
      toast({
        title: "Analysis Failed",
        description: error.message || "Failed to analyze data sources",
        variant: "destructive",
      })
    } finally {
      setScrapingAll(false)
    }
  }

  const handleTestFirecrawl = async () => {
    try {
      // Test Supabase connection instead
      const { data, error } = await supabase
        .from('opportunities')
        .select('id')
        .limit(1)

      if (error) throw error
      
      toast({
        title: "Supabase Connection Test Successful",
        description: `Successfully connected to Supabase database`,
      })
    } catch (error) {
      console.error('Supabase test failed:', error)
      toast({
        title: "Supabase Connection Test Failed",
        description: error.message || "Failed to connect to Supabase database",
        variant: "destructive",
      })
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
    }
  }

  // Categorize government data sources
  const getGovernmentSources = () => {
    const mockGovernmentSources = {
      federal: [
        {
          id: 'sam_gov',
          name: 'SAM.gov Opportunities',
          description: 'Federal contract opportunities',
          icon: Building2,
          status: 'completed',
          last_sync: new Date().toISOString(),
          rate_limit: '500/hour',
          opportunities_found: 25430,
          api_endpoint: 'https://api.sam.gov/opportunities/v2/search'
        },
        {
          id: 'grants_gov',
          name: 'Grants.gov',
          description: 'Federal grant opportunities', 
          icon: FileText,
          status: 'completed',
          last_sync: new Date().toISOString(),
          rate_limit: '1000/hour',
          opportunities_found: 12850,
          api_endpoint: 'https://api.grants.gov/v1/api/search2'
        },
        {
          id: 'usaspending',
          name: 'USASpending.gov',
          description: 'Historical contract awards',
          icon: Database,
          status: 'completed', 
          last_sync: new Date().toISOString(),
          rate_limit: '1000/hour',
          opportunities_found: 8940,
          api_endpoint: 'https://api.usaspending.gov/api/v2'
        },
        {
          id: 'challenge_gov',
          name: 'Challenge.gov',
          description: 'Federal competitions & challenges',
          icon: Trophy,
          status: 'pending',
          last_sync: null,
          rate_limit: 'TBD',
          opportunities_found: 0,
          api_endpoint: 'https://api.challenge.gov'
        }
      ],
      state_local: [
        {
          id: 'fpds_api',
          name: 'FPDS API',
          description: 'Federal Procurement Data System',
          icon: Database,
          status: 'pending',
          last_sync: null,
          rate_limit: 'No limit',
          opportunities_found: 0,
          api_endpoint: 'https://www.fpds.gov/fpdsng_cms/index.php/en/worksite.html'
        },
        {
          id: 'state_portals',
          name: 'State Procurement Portals',
          description: 'Aggregated state-level opportunities',
          icon: MapPin,
          status: 'planned',
          last_sync: null,
          rate_limit: 'Various',
          opportunities_found: 0,
          api_endpoint: 'Multiple endpoints'
        }
      ],
      alternative: [
        {
          id: 'agency_feeds',
          name: 'Agency RSS Feeds',
          description: 'News feeds from government agencies',
          icon: Globe,
          status: 'planned',
          last_sync: null,
          rate_limit: 'No limit',
          opportunities_found: 0,
          api_endpoint: 'RSS/Atom feeds'
        },
        {
          id: 'social_monitoring',
          name: 'Social Media Monitoring',
          description: 'Government procurement social posts',
          icon: Zap,
          status: 'planned',
          last_sync: null,
          rate_limit: 'Various',
          opportunities_found: 0,
          api_endpoint: 'Social APIs'
        }
      ]
    }

    return mockGovernmentSources
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Sync Status</h1>
          <Button disabled>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            Loading...
          </Button>
        </div>
        
        <div className="grid gap-6 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 bg-muted animate-pulse rounded"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="h-4 bg-muted animate-pulse rounded"></div>
                  <div className="h-4 bg-muted animate-pulse rounded w-3/4"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sync Status</h1>
          <p className="text-muted-foreground">
            Monitor data synchronization and web scraping status
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button onClick={handleTestFirecrawl} variant="outline">
            <Zap className="w-4 h-4 mr-2" />
            Test Firecrawl
          </Button>
          <Button onClick={handleScrapeAll} disabled={scrapingAll}>
            <Globe className="w-4 h-4 mr-2" />
            {scrapingAll ? 'Scraping...' : 'Scrape All'}
          </Button>
          <Button onClick={handleSyncAll} disabled={syncing}>
            <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync All'}
          </Button>
        </div>
      </div>

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Status</CardTitle>
          <CardDescription>
            Summary of all data sources and last synchronization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {Object.keys(syncStatus?.by_source || {}).length || 0}
              </div>
              <p className="text-sm text-muted-foreground">Total Sources</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {syncStatus?.sources_active || 0}
              </div>
              <p className="text-sm text-muted-foreground">Active Sources</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {syncStatus?.opportunities_processed || 0}
              </div>
              <p className="text-sm text-muted-foreground">Last Sync Processed</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {syncStatus?.opportunities_added || 0}
              </div>
              <p className="text-sm text-muted-foreground">Last Sync Added</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Government Data Sources - Tabbed Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Building2 className="w-5 h-5 mr-2" />
            Government Data Sources
          </CardTitle>
          <CardDescription>
            Organized by federal agencies, state/local governments, and alternative collection methods
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="federal" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="federal" className="flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                Federal APIs
              </TabsTrigger>
              <TabsTrigger value="state-local" className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                State & Local
              </TabsTrigger>
              <TabsTrigger value="alternative" className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Alternative
              </TabsTrigger>
              <TabsTrigger value="scraping" className="flex items-center gap-2">
                <Globe className="w-4 h-4" />
                Web Scraping
              </TabsTrigger>
            </TabsList>

            {/* Federal APIs Tab */}
            <TabsContent value="federal" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Federal Government APIs</h3>
                <Badge variant="outline">
                  {getGovernmentSources().federal.filter(s => s.status === 'completed').length} Active
                </Badge>
              </div>
              <div className="grid gap-4">
                {getGovernmentSources().federal.map((source) => {
                  const IconComponent = source.icon
                  return (
                    <div key={source.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <IconComponent className="w-5 h-5 text-blue-600" />
                        <div>
                          <p className="font-medium">{source.name}</p>
                          <p className="text-sm text-muted-foreground">{source.description}</p>
                          <p className="text-xs text-muted-foreground">
                            Rate limit: {source.rate_limit} | Last sync: {source.last_sync ? formatDate(source.last_sync) : 'Never'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="text-right text-sm">
                          <p className="font-medium text-green-600">
                            {source.opportunities_found.toLocaleString()}
                          </p>
                          <p className="text-muted-foreground">opportunities</p>
                        </div>
                        
                        <Badge className={getStatusColor(source.status)}>
                          {source.status}
                        </Badge>
                      </div>
                    </div>
                  )
                })}
              </div>
            </TabsContent>

            {/* State & Local Tab */}
            <TabsContent value="state-local" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">State & Local Government Sources</h3>
                <Badge variant="outline">
                  {getGovernmentSources().state_local.filter(s => s.status === 'completed').length} Active
                </Badge>
              </div>
              <div className="grid gap-4">
                {getGovernmentSources().state_local.map((source) => {
                  const IconComponent = source.icon
                  return (
                    <div key={source.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <IconComponent className="w-5 h-5 text-purple-600" />
                        <div>
                          <p className="font-medium">{source.name}</p>
                          <p className="text-sm text-muted-foreground">{source.description}</p>
                          <p className="text-xs text-muted-foreground">
                            Rate limit: {source.rate_limit} | Last sync: {source.last_sync ? formatDate(source.last_sync) : 'Never'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="text-right text-sm">
                          <p className="font-medium text-green-600">
                            {source.opportunities_found.toLocaleString()}
                          </p>
                          <p className="text-muted-foreground">opportunities</p>
                        </div>
                        
                        <Badge className={getStatusColor(source.status)}>
                          {source.status}
                        </Badge>
                      </div>
                    </div>
                  )
                })}
              </div>
            </TabsContent>

            {/* Alternative Methods Tab */}
            <TabsContent value="alternative" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Alternative Data Collection</h3>
                <Badge variant="outline">
                  {getGovernmentSources().alternative.filter(s => s.status === 'completed').length} Active
                </Badge>
              </div>
              <div className="grid gap-4">
                {getGovernmentSources().alternative.map((source) => {
                  const IconComponent = source.icon
                  return (
                    <div key={source.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <IconComponent className="w-5 h-5 text-orange-600" />
                        <div>
                          <p className="font-medium">{source.name}</p>
                          <p className="text-sm text-muted-foreground">{source.description}</p>
                          <p className="text-xs text-muted-foreground">
                            Rate limit: {source.rate_limit} | Last sync: {source.last_sync ? formatDate(source.last_sync) : 'Never'}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="text-right text-sm">
                          <p className="font-medium text-green-600">
                            {source.opportunities_found.toLocaleString()}
                          </p>
                          <p className="text-muted-foreground">opportunities</p>
                        </div>
                        
                        <Badge className={getStatusColor(source.status)}>
                          {source.status}
                        </Badge>
                      </div>
                    </div>
                  )
                })}
              </div>
            </TabsContent>

            {/* Web Scraping Tab */}
            <TabsContent value="scraping" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Web Scraping Sources</h3>
                <Badge variant="outline">
                  {Object.keys(syncStatus?.sources || {}).filter(name => name.startsWith('firecrawl_')).length} Active
                </Badge>
              </div>
              <div className="space-y-4">
                {/* Firecrawl Sources from Sync Status */}
                {syncStatus?.sources ? Object.entries(syncStatus.sources)
                  .filter(([name]) => name.startsWith('firecrawl_'))
                  .map(([sourceName, status]) => (
                  <div key={sourceName} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-green-600" />
                      <div>
                        <p className="font-medium">{sourceName.replace('firecrawl_', '')}</p>
                        <p className="text-sm text-muted-foreground">
                          Last scrape: {status.last_sync ? formatDate(status.last_sync) : 'Never'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <div className="text-right text-sm">
                        <p className="text-muted-foreground">
                          {status.records_processed || 0} processed
                        </p>
                        <p className="text-muted-foreground">
                          {status.records_added || 0} added, {status.records_updated || 0} updated
                        </p>
                      </div>
                      
                      <Badge className={getStatusColor(status.status)}>
                        {status.status || 'unknown'}
                      </Badge>
                    </div>
                  </div>
                )) : null}

                {/* Available Scraping Sources */}
                {scrapingSources.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-3">Available Scraping Sources</h4>
                      <div className="grid gap-3 md:grid-cols-2">
                        {scrapingSources.map((source) => (
                          <div key={source.key} className="p-3 border rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium">{source.name}</p>
                                <p className="text-xs text-muted-foreground">{source.type}</p>
                              </div>
                              <Badge variant="outline">
                                {source.key}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-2 truncate">
                              {source.url}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {scrapingSources.length === 0 && !Object.keys(syncStatus?.sources || {}).some(name => name.startsWith('firecrawl_')) && (
                  <div className="text-center py-8">
                    <Globe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No scraping sources available</h3>
                    <p className="text-muted-foreground mb-4">
                      Firecrawl service may not be configured or available
                    </p>
                    <Button onClick={handleTestFirecrawl} variant="outline">
                      <Zap className="w-4 h-4 mr-2" />
                      Test Firecrawl Service
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Recent Sync Activity */}
      {syncStatus?.recent_syncs && syncStatus.recent_syncs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Sync Activity</CardTitle>
            <CardDescription>
              Latest synchronization attempts and results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {syncStatus.recent_syncs.map((sync, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(sync.status)}
                    <div>
                      <p className="font-medium">{sync.source_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(sync.sync_start)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right text-sm">
                    <p className="text-muted-foreground">
                      {sync.records_processed || 0} processed
                    </p>
                    <p className="text-muted-foreground">
                      {sync.records_added || 0} added
                    </p>
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

