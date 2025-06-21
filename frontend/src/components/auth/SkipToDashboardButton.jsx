import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { ArrowRight, Zap } from 'lucide-react'

export const SkipToDashboardButton = () => {
  const navigate = useNavigate()

  const handleSkipToDashboard = () => {
    // Create a mock user session in localStorage to bypass auth
    const mockUser = {
      id: 'demo-user-123',
      email: 'demo@opportunitydashboard.com',
      user_metadata: {
        full_name: 'Demo User',
        company: 'Demo Company',
        role: 'business_owner'
      },
      created_at: new Date().toISOString(),
      email_confirmed_at: new Date().toISOString()
    }

    // Store mock session
    localStorage.setItem('demo-mode', 'true')
    localStorage.setItem('demo-user', JSON.stringify(mockUser))
    
    // Navigate to dashboard
    navigate('/dashboard')
    
    // Reload to trigger auth context update
    window.location.reload()
  }

  return (
    <Card className="w-full max-w-md mx-auto mt-6 border-green-200 bg-green-50 dark:bg-green-950 dark:border-green-800">
      <CardHeader className="text-center pb-4">
        <CardTitle className="text-lg flex items-center justify-center gap-2 text-green-700 dark:text-green-300">
          <Zap className="h-5 w-5" />
          Quick Demo Access
        </CardTitle>
        <CardDescription className="text-green-600 dark:text-green-400">
          Skip login and go straight to the dashboard
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-0">
        <Button
          onClick={handleSkipToDashboard}
          className="w-full bg-green-600 hover:bg-green-700 text-white"
          size="lg"
        >
          <ArrowRight className="mr-2 h-4 w-4" />
          Skip to Dashboard
        </Button>
        
        <div className="mt-3 text-xs text-green-600 dark:text-green-400 text-center">
          No login required • Instant access to all features
        </div>
      </CardContent>
    </Card>
  )
} 