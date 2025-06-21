import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { LoginForm } from '../components/auth/LoginForm'
import { DemoLoginButton } from '../components/auth/DemoLoginButton'
import { SkipToDashboardButton } from '../components/auth/SkipToDashboardButton'
import { useAuth } from '../contexts/AuthContext'

export const LoginPage = () => {
  const { user } = useAuth()
  const location = useLocation()

  // If user is already logged in, redirect to dashboard or intended page
  if (user) {
    const from = location.state?.from?.pathname || '/dashboard'
    return <Navigate to={from} replace />
  }

  const handleLoginSuccess = () => {
    // Navigation will be handled by the AuthContext and ProtectedRoute
    const from = location.state?.from?.pathname || '/dashboard'
    window.location.href = from
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Opportunity Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Your gateway to federal contracting opportunities
          </p>
        </div>
        
        <LoginForm onSuccess={handleLoginSuccess} />
        
        <DemoLoginButton />
        
        <SkipToDashboardButton />
      </div>
    </div>
  )
} 