import React, { useState } from 'react'
import { Brain, TrendingUp, Target, Users, Zap, Search, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '../hooks/use-toast'
import { apiClient } from '../lib/api'

export default function PerplexityPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

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

      {/* Search Interface */}
      <Card className="mb-8">
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
        <Card className="mb-8">
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-500" />
              Market Analysis
            </CardTitle>
            <CardDescription>
              AI-powered market trend analysis and insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Get comprehensive market analysis, competitor insights, and trend forecasting using advanced AI.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ Now Available
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Opportunity Scoring
            </CardTitle>
            <CardDescription>
              Smart scoring and ranking of opportunities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI analyzes opportunities and provides intelligent scoring based on your profile and market conditions.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ Advanced Features Available
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-500" />
              Competitive Analysis
            </CardTitle>
            <CardDescription>
              Analyze competitive landscape and positioning
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Understand market competition, key players, and winning strategies for government contracts.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ AI Analysis Ready
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-orange-500" />
              Smart Alerts
            </CardTitle>
            <CardDescription>
              Intelligent opportunity alerts and predictions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Receive AI-powered alerts about new opportunities matching your profile and interests.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ Prediction Engine Active
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Market Forecasting
            </CardTitle>
            <CardDescription>
              Predict future market conditions and trends
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI-powered forecasting of government contracting markets and upcoming opportunities.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ Forecasting Models Deployed
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-indigo-500" />
              Compliance Analysis
            </CardTitle>
            <CardDescription>
              Analyze regulatory and compliance requirements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              AI analyzes compliance requirements and regulatory landscape for opportunities.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ✅ Compliance Engine Ready
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}