import { useState, useEffect } from 'react'
import { createBrowserRouter, RouterProvider, Route, createRoutesFromElements, Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import Sidebar from '@/components/Sidebar'
import Dashboard from '@/components/Dashboard'
import OpportunityList from '@/components/OpportunityList'
import OpportunityDetail from '@/components/OpportunityDetail'
import SearchPage from '@/components/SearchPage'
import PerplexityPage from '@/components/PerplexityPage'
import SettingsPage from '@/components/SettingsPage'
import SyncStatus from '@/components/SyncStatus'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage'
import './App.css'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      setDarkMode(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    if (!darkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  // Create a layout component to wrap all routes
  const AppLayout = () => {
    return (
      <div className={`min-h-screen bg-background text-foreground ${darkMode ? 'dark' : ''}`}>
        <div className="flex">
          <Sidebar 
            isOpen={sidebarOpen} 
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            darkMode={darkMode}
            onToggleDarkMode={toggleDarkMode}
          />
          
          <main className={`flex-1 transition-all duration-300 ${
            sidebarOpen ? 'ml-64' : 'ml-16'
          }`}>
            <div className="p-6">
              {/* Outlet will be injected by React Router */}
              <Outlet />
            </div>
          </main>
        </div>
        
        <Toaster />
      </div>
    );
  };
  
  // Create router configuration
  const router = createBrowserRouter(
    createRoutesFromElements(
      <>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        
        {/* Protected routes */}
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/opportunities" element={<OpportunityList />} />
          <Route path="/opportunities/:id" element={<OpportunityDetail />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/perplexity" element={<PerplexityPage />} />
          <Route path="/sync" element={<SyncStatus />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </>
    )
  );

  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  )
}

export default App

