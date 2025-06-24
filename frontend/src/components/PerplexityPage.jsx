import React from 'react'
import { Brain, TrendingUp, Target, Users, Zap } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function PerplexityPage() {
  return (
    <div className="container mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          🧠 AI Market Intelligence
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Advanced market intelligence and analysis tools (Coming Soon)
        </p>
      </div>

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
              Get comprehensive market analysis, competitor insights, and trend forecasting.
            </p>
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                ⚡ Feature coming soon
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
              Advanced algorithms to score and rank opportunities based on your criteria.
            </p>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-sm text-green-700 dark:text-green-300">
                ⚡ Feature coming soon
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-500" />
              Competitive Intelligence
            </CardTitle>
            <CardDescription>
              Track competitors and market positioning
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Monitor competitor activities and market positioning strategies.
            </p>
            <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-sm text-purple-700 dark:text-purple-300">
                ⚡ Feature coming soon
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-orange-500" />
              Market Mapping
            </CardTitle>
            <CardDescription>
              Visualize market landscape and relationships
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Interactive maps showing market relationships and key players.
            </p>
            <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <p className="text-sm text-orange-700 dark:text-orange-300">
                ⚡ Feature coming soon
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Smart Alerts
            </CardTitle>
            <CardDescription>
              Automated notifications for market changes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Get notified when market conditions change or new opportunities arise.
            </p>
            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                ⚡ Feature coming soon
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-indigo-500" />
              Predictive Analytics
            </CardTitle>
            <CardDescription>
              AI predictions for market movements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Use machine learning to predict future market trends and opportunities.
            </p>
            <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <p className="text-sm text-indigo-700 dark:text-indigo-300">
                ⚡ Feature coming soon
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <Card>
          <CardHeader>
            <CardTitle>Development Status</CardTitle>
            <CardDescription>
              Current progress on AI intelligence features
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Core Dashboard</span>
                <span className="text-sm text-green-600 font-medium">✅ Complete</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Opportunity Tracking</span>
                <span className="text-sm text-green-600 font-medium">✅ Complete</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">AI Market Intelligence</span>
                <span className="text-sm text-yellow-600 font-medium">🚧 In Development</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Advanced Analytics</span>
                <span className="text-sm text-gray-500 font-medium">⏳ Planned</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}