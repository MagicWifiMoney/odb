import React from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { RegisterForm } from '../components/auth/RegisterForm'
import { useAuth } from '../contexts/AuthContext'

export const RegisterPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  // If user is already logged in, redirect to dashboard
  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  const handleRegisterSuccess = () => {
    // Redirect to login page after successful registration
    navigate('/login', { 
      state: { 
        message: 'Account created successfully! Please check your email to verify your account.' 
      } 
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Join Opportunity Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Create your account to start discovering opportunities
          </p>
        </div>
        
        <RegisterForm onSuccess={handleRegisterSuccess} />
      </div>
    </div>
  )
} 