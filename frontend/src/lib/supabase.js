import { createClient } from '@supabase/supabase-js'

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://zkdrpchjejelgsuuffli.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InprZHJwY2hqZWplbGdzdXVmZmxpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyMjY4MTMsImV4cCI6MjA2NTgwMjgxM30.xBBArkhXeFT26BmVI-WNag0qa0hHGdFUmxmlcTi4CGg'

// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Log configuration
console.log('Supabase configured with URL:', supabaseUrl) 