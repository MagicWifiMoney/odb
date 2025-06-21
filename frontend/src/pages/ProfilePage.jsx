import React from 'react'
import { UserProfile } from '../components/auth/UserProfile'

export const ProfilePage = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Account Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">
            Manage your profile and dashboard preferences
          </p>
        </div>
        
        <UserProfile />
      </div>
    </div>
  )
} 