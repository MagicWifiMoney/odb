
import { supabase } from './src/lib/supabase.js'

async function testSupabase() {
  console.log('Testing Supabase connection...')
  
  // Get a few opportunities to see the data structure
  const { data, error, count } = await supabase
    .from('opportunities')
    .select('id, title, agency_name')
    .limit(5)
  
  if (error) {
    console.error('Supabase error:', error)
  } else {
    console.log('Found', count, 'opportunities total')
    console.log('Sample opportunities:', data)
    console.log('ID types:', data?.map(d => typeof d.id))
  }
}

testSupabase().catch(console.error)

