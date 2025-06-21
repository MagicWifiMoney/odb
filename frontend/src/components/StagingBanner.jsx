import { AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription } from './ui/alert'

export default function StagingBanner() {
  // Check if we're in staging environment
  const isStaging = import.meta.env.VITE_ENVIRONMENT === 'staging' || 
                   window.location.hostname.includes('staging') ||
                   window.location.hostname.includes('preview')

  if (!isStaging) {
    return null
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <Alert className="border-orange-200 bg-orange-50 text-orange-800 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-200">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription className="flex items-center justify-between">
          <span className="font-semibold">
            🧪 STAGING ENVIRONMENT - This is a test version
          </span>
          <span className="text-xs opacity-75">
            Data may be reset frequently
          </span>
        </AlertDescription>
      </Alert>
    </div>
  )
} 