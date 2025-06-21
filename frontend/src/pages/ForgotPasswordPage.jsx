import React from 'react'
import { Navigate } from 'react-router-dom'
import { ForgotPasswordForm } from '../components/auth/ForgotPasswordForm'
import { useAuth } from '../contexts/AuthContext'

export const ForgotPasswordPage = () => {
  const { user } = useAuth()

  // If user is already logged in, redirect to dashboard
  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Opportunity Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Reset your password to regain access
          </p>
        </div>
        
        <ForgotPasswordForm />
      </div>
    </div>
  )
} 