import React, { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { useToast } from '../hooks/use-toast'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [session, setSession] = useState(null)
  const { toast } = useToast()

  useEffect(() => {
    // Check for demo mode first
    const isDemoMode = localStorage.getItem('demo-mode') === 'true'
    const demoUser = localStorage.getItem('demo-user')
    
    if (isDemoMode && demoUser) {
      try {
        const parsedUser = JSON.parse(demoUser)
        setUser(parsedUser)
        setSession({ user: parsedUser })
        setLoading(false)
        return
      } catch (error) {
        console.error('Error parsing demo user:', error)
        localStorage.removeItem('demo-mode')
        localStorage.removeItem('demo-user')
      }
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)

      if (event === 'SIGNED_IN') {
        toast({
          title: "Welcome back!",
          description: "You have been successfully signed in.",
        })
      } else if (event === 'SIGNED_OUT') {
        toast({
          title: "Signed out",
          description: "You have been successfully signed out.",
        })
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const signUp = async (email, password, metadata = {}) => {
    try {
      setLoading(true)
      
      // Check if this is a demo account
      const isDemoAccount = email === 'demo@opportunitydashboard.com'
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: metadata.full_name || '',
            company: metadata.company || '',
            role: metadata.role || '',
          },
          // Skip email confirmation for demo account
          emailRedirectTo: isDemoAccount ? undefined : `${window.location.origin}/dashboard`
        }
      })

      if (error) throw error

      if (isDemoAccount) {
        toast({
          title: "Demo account ready!",
          description: "You can now sign in with the demo credentials.",
        })
      } else {
        toast({
          title: "Account created!",
          description: "Please check your email to verify your account.",
        })
      }

      return { data, error: null }
    } catch (error) {
      console.error('Sign up error:', error)
      toast({
        title: "Sign up failed",
        description: error.message,
        variant: "destructive",
      })
      return { data: null, error }
    } finally {
      setLoading(false)
    }
  }

  const signIn = async (email, password) => {
    try {
      setLoading(true)
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) throw error

      return { data, error: null }
    } catch (error) {
      console.error('Sign in error:', error)
      toast({
        title: "Sign in failed",
        description: error.message,
        variant: "destructive",
      })
      return { data: null, error }
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    try {
      setLoading(true)
      
      // Handle demo mode signout
      const isDemoMode = localStorage.getItem('demo-mode') === 'true'
      if (isDemoMode) {
        localStorage.removeItem('demo-mode')
        localStorage.removeItem('demo-user')
        setUser(null)
        setSession(null)
        toast({
          title: "Signed out",
          description: "You have been successfully signed out of demo mode.",
        })
        return
      }
      
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    } catch (error) {
      console.error('Sign out error:', error)
      toast({
        title: "Sign out failed",
        description: error.message,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const resetPassword = async (email) => {
    try {
      const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) throw error

      toast({
        title: "Password reset sent",
        description: "Check your email for the password reset link.",
      })

      return { data, error: null }
    } catch (error) {
      console.error('Password reset error:', error)
      toast({
        title: "Password reset failed",
        description: error.message,
        variant: "destructive",
      })
      return { data: null, error }
    }
  }

  const updateProfile = async (updates) => {
    try {
      const { data, error } = await supabase.auth.updateUser({
        data: updates
      })

      if (error) throw error

      toast({
        title: "Profile updated",
        description: "Your profile has been successfully updated.",
      })

      return { data, error: null }
    } catch (error) {
      console.error('Profile update error:', error)
      toast({
        title: "Profile update failed",
        description: error.message,
        variant: "destructive",
      })
      return { data: null, error }
    }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updateProfile,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 