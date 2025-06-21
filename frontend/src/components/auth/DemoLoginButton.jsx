import React, { useState } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { User, Zap } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export const DemoLoginButton = () => {
  const [isLoading, setIsLoading] = useState(false)
  const { signIn, signUp } = useAuth()

  const handleDemoLogin = async () => {
    setIsLoading(true)
    
    // Demo account credentials
    const demoEmail = 'demo@opportunitydashboard.com'
    const demoPassword = 'demo123456'
    
    try {
      // Try to sign in with demo account first
      const { data: signInData, error: signInError } = await signIn(demoEmail, demoPassword)
      
      if (signInError && signInError.message.includes('Invalid login credentials')) {
        // If demo account doesn't exist, create it
        console.log('Demo account not found, creating...')
        
        const { data: signUpData, error: signUpError } = await signUp(
          demoEmail,
          demoPassword,
          {
            full_name: 'Demo User',
            company: 'Demo Company',
            role: 'business_owner',
          }
        )
        
        if (signUpError) {
          throw signUpError
        }
        
        // If signup successful, try signing in again
        if (signUpData) {
          const { error: secondSignInError } = await signIn(demoEmail, demoPassword)
          if (secondSignInError) {
            throw secondSignInError
          }
        }
      } else if (signInError) {
        throw signInError
      }
      
    } catch (error) {
      console.error('Demo login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto mt-6 border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
      <CardHeader className="text-center pb-4">
        <CardTitle className="text-lg flex items-center justify-center gap-2 text-blue-700 dark:text-blue-300">
          <Zap className="h-5 w-5" />
          Quick Demo Access
        </CardTitle>
        <CardDescription className="text-blue-600 dark:text-blue-400">
          Skip registration and try the dashboard instantly
        </CardDescription>
      </CardHeader>
      
      <CardContent className="pt-0">
        <Button
          onClick={handleDemoLogin}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
          size="lg"
        >
          {isLoading ? (
            'Setting up demo...'
          ) : (
            <>
              <User className="mr-2 h-4 w-4" />
              Login as Demo User
            </>
          )}
        </Button>
        
        <div className="mt-3 text-xs text-blue-600 dark:text-blue-400 text-center">
          Demo credentials: demo@opportunitydashboard.com
        </div>
      </CardContent>
    </Card>
  )
} 