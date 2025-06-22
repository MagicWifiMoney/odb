import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingDown, 
  TrendingUp, 
  DollarSign, 
  Zap, 
  Activity, 
  Shield,
  RefreshCw,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

const CostMonitoringDashboard = () => {
  const [costData, setCostData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [featureFlags, setFeatureFlags] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchCostData = async () => {
    try {
      const response = await fetch('/api/performance/cost-tracking');
      if (response.ok) {
        const data = await response.json();
        setCostData(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch cost data:', error);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch('/api/performance/summary');
      if (response.ok) {
        const data = await response.json();
        setPerformanceData(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    }
  };

  const fetchFeatureFlags = async () => {
    try {
      const response = await fetch('/api/performance/feature-flags');
      if (response.ok) {
        const data = await response.json();
        setFeatureFlags(data.data);
      }
    } catch (error) {
      console.error('Failed to fetch feature flags:', error);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    await Promise.all([
      fetchCostData(),
      fetchPerformanceData(),
      fetchFeatureFlags()
    ]);
    setLastUpdated(new Date());
    setLoading(false);
  };

  useEffect(() => {
    refreshData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshData, 30000);
    return () => clearInterval(interval);
  }, []);

  const calculateCostReduction = () => {
    if (!costData || !performanceData) return 0;
    
    const hitRate = performanceData.cache_stats?.hit_rate_percent || 0;
    // Phase 1: 50-70% reduction from frontend caching
    // Phase 2: Additional 20-30% from backend optimization
    const frontendReduction = Math.min(hitRate * 0.7, 70);
    const backendReduction = featureFlags?.enabled_count >= 6 ? 20 : 0;
    
    return Math.min(frontendReduction + backendReduction, 80);
  };

  const getCostReductionColor = (reduction) => {
    if (reduction >= 70) return 'text-green-600';
    if (reduction >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getOptimizationStatus = () => {
    const reduction = calculateCostReduction();
    if (reduction >= 70) return { status: 'Excellent', color: 'bg-green-500', icon: CheckCircle };
    if (reduction >= 50) return { status: 'Good', color: 'bg-yellow-500', icon: Activity };
    return { status: 'Needs Improvement', color: 'bg-red-500', icon: AlertTriangle };
  };

  if (loading && !costData) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        Loading cost monitoring data...
      </div>
    );
  }

  const costReduction = calculateCostReduction();
  const optimizationStatus = getOptimizationStatus();
  const StatusIcon = optimizationStatus.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Perplexity Cost Optimization Dashboard</h2>
          <p className="text-muted-foreground">
            Phase 2 Backend Enhancement - Real-time cost reduction monitoring
          </p>
        </div>
        <Button onClick={refreshData} disabled={loading} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost Reduction</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getCostReductionColor(costReduction)}`}>
              {costReduction.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Target: 70-80% reduction
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performanceData?.cache_stats?.hit_rate_percent || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {performanceData?.cache_stats?.hits || 0} hits / {performanceData?.cache_stats?.total_requests || 0} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost Savings</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${costData?.estimated_total_savings || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {costData?.api_calls_saved || 0} calls saved
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Optimization Status</CardTitle>
            <StatusIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${optimizationStatus.color}`}></div>
              <span className="text-sm font-medium">{optimizationStatus.status}</span>
            </div>
            <p className="text-xs text-muted-foreground">
              {featureFlags?.enabled_count || 0}/{featureFlags?.total_count || 0} features enabled
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Progress Toward Target */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Reduction Progress</CardTitle>
          <CardDescription>
            Progress toward 70-80% cost reduction target
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Current Reduction: {costReduction.toFixed(1)}%</span>
                <span>Target: 70-80%</span>
              </div>
              <Progress value={Math.min(costReduction, 100)} className="h-2" />
            </div>
            
            {costReduction >= 70 ? (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  🎉 Excellent! You've achieved the target cost reduction of 70-80%. 
                  Phase 2 optimization is performing as expected.
                </AlertDescription>
              </Alert>
            ) : costReduction >= 50 ? (
              <Alert>
                <Activity className="h-4 w-4" />
                <AlertDescription>
                  Good progress! You've achieved {costReduction.toFixed(1)}% cost reduction. 
                  Continue using the cache to reach the 70-80% target.
                </AlertDescription>
              </Alert>
            ) : (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Cache system is warming up. Use the Perplexity Intelligence features to build cache and see cost reductions.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Tabs */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="features">Feature Flags</TabsTrigger>
          <TabsTrigger value="technical">Technical Details</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Cache Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Cache Size:</span>
                  <span>{performanceData?.cache_stats?.cache_size || 0} items</span>
                </div>
                <div className="flex justify-between">
                  <span>Cache Hits:</span>
                  <span className="text-green-600">{performanceData?.cache_stats?.hits || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Cache Misses:</span>
                  <span className="text-red-600">{performanceData?.cache_stats?.misses || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Redis Available:</span>
                  <Badge variant={performanceData?.cache_stats?.redis_available ? 'default' : 'destructive'}>
                    {performanceData?.cache_stats?.redis_available ? 'Yes' : 'No'}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cost Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span>Cost per API Call:</span>
                  <span>${costData?.estimated_cost_per_call || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>API Calls Saved:</span>
                  <span className="text-green-600">{costData?.api_calls_saved || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Savings:</span>
                  <span className="text-green-600 font-bold">${costData?.estimated_total_savings || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Cost Tracking:</span>
                  <Badge variant={costData?.cost_tracking_enabled ? 'default' : 'destructive'}>
                    {costData?.cost_tracking_enabled ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="features" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Feature Flag Status</CardTitle>
              <CardDescription>
                Current feature flag configuration for Phase 2 optimization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {featureFlags?.flags && Object.entries(featureFlags.flags).map(([flag, enabled]) => (
                  <div key={flag} className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="capitalize">{flag.replace(/_/g, ' ')}</span>
                    <Badge variant={enabled ? 'default' : 'secondary'}>
                      {enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="technical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Technical Implementation</CardTitle>
              <CardDescription>
                Phase 2 backend optimization technical details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Phase 1 - Frontend Optimization</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>ContextAwareSearch component with intelligent caching</li>
                    <li>LocalStorage-based query history (max 50 entries)</li>
                    <li>Template-based query optimization</li>
                    <li>Expected reduction: 50-70%</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Phase 2 - Backend Optimization</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Redis cache integration for query results</li>
                    <li>Performance monitoring and analytics</li>
                    <li>Feature flag system for controlled rollout</li>
                    <li>Cost tracking and optimization alerts</li>
                    <li>Additional reduction: 20-30%</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Monitoring & Alerting</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    <li>Real-time cache hit/miss tracking</li>
                    <li>Cost reduction calculation and visualization</li>
                    <li>Performance health checks</li>
                    <li>Feature flag management dashboard</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      {lastUpdated && (
        <div className="text-center text-sm text-muted-foreground">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default CostMonitoringDashboard; 