import { useState, useEffect } from 'react'
import { Search, Filter, Calendar, DollarSign, Target } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Slider } from './ui/slider'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { AlertCircle, Clock, Building, MapPin, Users, ExternalLink } from 'lucide-react'
import { Alert, AlertDescription } from './ui/alert'
import { formatCurrency, formatDate, formatRelativeDate, getScoreColor, getScoreBadgeColor, getUrgencyColor, getSourceTypeLabel, getSourceTypeColor } from '../lib/api'
import { useToast } from '../hooks/use-toast'
import { supabase } from '../lib/supabase'

export default function SearchPage() {
  const [searchForm, setSearchForm] = useState({
    keywords: '',
    minValue: '',
    maxValue: '',
    postedSince: '',
    dueBy: '',
    sourceType: 'all',
    minScore: ''
  })
  
  const [searchResults, setSearchResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)

  // Search state
  const [totalResults, setTotalResults] = useState(0)
  const [searchTime, setSearchTime] = useState(0)

  const { toast } = useToast()

  const handleInputChange = (field, value) => {
    setSearchForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const searchOpportunities = async () => {
    if (!searchForm.keywords.trim()) {
      setError('Please enter search keywords')
      return
    }

    setIsLoading(true)
    setError(null)
    setHasSearched(true)
    const startTime = Date.now()

    try {
      // First, let's check what tables exist in the database
      const { data: tables, error: tablesError } = await supabase
        .from('information_schema.tables')
        .select('table_name')
        .eq('table_schema', 'public')

      if (tablesError) {
        console.log('Tables query error:', tablesError)
        // Try a simpler approach - just check if opportunities table exists
        const { data, error: simpleError } = await supabase
          .from('opportunities')
          .select('*')
          .limit(1)

        if (simpleError) {
          throw new Error(`Database setup needed. Error: ${simpleError.message}`)
        }
      } else {
        console.log('Available tables:', tables)
      }

      // If we get here, try to search the opportunities table
      let query = supabase
        .from('opportunities')
        .select('*')

      // Apply text search on multiple columns - start with basic columns
      if (searchForm.keywords.trim()) {
        const keywords = searchForm.keywords.trim()
        // Start with basic search that should work with most schemas
        query = query.or(`title.ilike.%${keywords}%,description.ilike.%${keywords}%`)
      }

      // Apply basic filters only
      if (searchForm.minValue) {
        const minValue = parseFloat(searchForm.minValue)
        if (!isNaN(minValue)) {
          query = query.gte('estimated_value', minValue)
        }
      }

      // Limit results for testing
      query = query.limit(10)

      const { data, error: supabaseError } = await query

      if (supabaseError) {
        throw new Error(supabaseError.message)
      }

      const endTime = Date.now()
      setSearchTime(endTime - startTime)
      setSearchResults(data || [])
      setTotalResults(data?.length || 0)

      // Log the first result to see the actual schema
      if (data && data.length > 0) {
        console.log('Sample opportunity data:', data[0])
        console.log('Available columns:', Object.keys(data[0]))
      }

    } catch (err) {
      console.error('Search error:', err)
      setError(`Search Failed: ${err.message}`)
      setSearchResults([])
      setTotalResults(0)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    searchOpportunities()
  }

  const clearSearch = () => {
    setSearchForm({
      keywords: '',
      minValue: '',
      maxValue: '',
      postedSince: '',
      dueBy: '',
      sourceType: 'all',
      minScore: ''
    })
    setSearchResults([])
    setError(null)
    setHasSearched(false)
    setTotalResults(0)
    setSearchTime(0)
  }

  const openOpportunity = (url) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Advanced Search</h1>
        <p className="text-muted-foreground">
          Find opportunities using detailed criteria and filters
        </p>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Search Criteria
          </CardTitle>
          <CardDescription>
            Use the filters below to find opportunities that match your requirements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Keywords and Basic Filters */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords</Label>
                <Input
                  id="keywords"
                  placeholder="software, development, consulting (comma-separated)"
                  value={searchForm.keywords}
                  onChange={(e) => handleInputChange('keywords', e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Separate multiple keywords with commas
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="minValue">Minimum Value ($)</Label>
                <Input
                  id="minValue"
                  type="number"
                  placeholder="10000"
                  value={searchForm.minValue}
                  onChange={(e) => handleInputChange('minValue', e.target.value)}
                />
              </div>
            </div>

            {/* Score and Value Filters */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Minimum Score: {searchForm.minScore}</Label>
                <Slider
                  value={[parseFloat(searchForm.minScore) || 0]}
                  onValueChange={(value) => handleInputChange('minScore', value[0].toString())}
                  max={100}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0</span>
                  <span>50</span>
                  <span>100</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="maxValue">Maximum Value ($)</Label>
                <Input
                  id="maxValue"
                  type="number"
                  placeholder="1000000"
                  value={searchForm.maxValue}
                  onChange={(e) => handleInputChange('maxValue', e.target.value)}
                />
              </div>
            </div>

            {/* Category and Source Filters */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Posted Since</Label>
                <Input
                  id="postedSince"
                  type="date"
                  value={searchForm.postedSince}
                  onChange={(e) => handleInputChange('postedSince', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Due By</Label>
                <Input
                  id="dueBy"
                  type="date"
                  value={searchForm.dueBy}
                  onChange={(e) => handleInputChange('dueBy', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Source Type</Label>
                <Select 
                  value={searchForm.sourceType} 
                  onValueChange={(value) => handleInputChange('sourceType', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sources</SelectItem>
                    <SelectItem value="federal_contract">Federal Contract</SelectItem>
                    <SelectItem value="federal_grant">Federal Grant</SelectItem>
                    <SelectItem value="state_rfp">State RFP</SelectItem>
                    <SelectItem value="private_rfp">Private RFP</SelectItem>
                    <SelectItem value="scraped">Web Scraped</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Separator />

            {/* Action Buttons */}
            <div className="flex items-center space-x-4">
              <Button onClick={handleSubmit} disabled={isLoading}>
                <Search className="w-4 h-4 mr-2" />
                {isLoading ? 'Searching...' : 'Search Opportunities'}
              </Button>
              <Button variant="outline" onClick={clearSearch}>
                Clear All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      {hasSearched && (
        <Card>
          <CardHeader>
            <CardTitle>Search Results</CardTitle>
            <CardDescription>
              {isLoading ? 'Searching...' : `Found ${totalResults} opportunities in ${searchTime}ms`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="p-4 border rounded-lg">
                    <div className="space-y-3">
                      <div className="h-6 bg-muted animate-pulse rounded"></div>
                      <div className="h-4 bg-muted animate-pulse rounded w-3/4"></div>
                      <div className="flex space-x-2">
                        <div className="h-6 bg-muted animate-pulse rounded w-16"></div>
                        <div className="h-6 bg-muted animate-pulse rounded w-20"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : error ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {error}
                </AlertDescription>
              </Alert>
            ) : totalResults > 0 ? (
              <div className="space-y-4">
                {searchResults.map((opportunity) => (
                  <div key={opportunity.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-semibold">{opportunity.title}</h3>
                      <Badge className={getScoreBadgeColor(opportunity.relevance_score)}>
                        <Target className="w-3 h-3 mr-1" />
                        {opportunity.relevance_score}
                      </Badge>
                    </div>

                    <p className="text-muted-foreground mb-3 line-clamp-2">
                      {opportunity.description || 'No description available'}
                    </p>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div>
                        <p className="text-xs text-muted-foreground">Agency</p>
                        <p className="text-sm font-medium truncate">
                          {opportunity.agency_name || 'Unknown'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-muted-foreground">Value</p>
                        <p className="text-sm font-medium">
                          {opportunity.estimated_value ? formatCurrency(opportunity.estimated_value) : 'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-muted-foreground">Due Date</p>
                        <p className={`text-sm font-medium ${getUrgencyColor(opportunity.due_date)}`}>
                          {opportunity.due_date ? formatRelativeDate(opportunity.due_date) : 'N/A'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-muted-foreground">Source</p>
                        <Badge variant="outline" className={getSourceTypeColor(opportunity.source_type)}>
                          {getSourceTypeLabel(opportunity.source_type)}
                        </Badge>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {(() => {
                          // Handle different keyword formats
                          let keywords = [];
                          if (opportunity.keywords) {
                            if (Array.isArray(opportunity.keywords)) {
                              keywords = opportunity.keywords;
                            } else if (typeof opportunity.keywords === 'string') {
                              keywords = opportunity.keywords.split(',').map(k => k.trim()).filter(k => k);
                            }
                          }
                          
                          return (
                            <>
                              {keywords.slice(0, 3).map((keyword, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {keyword}
                                </Badge>
                              ))}
                              {keywords.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{keywords.length - 3} more
                                </Badge>
                              )}
                            </>
                          )
                        })()}
                      </div>

                      <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                        <span>R: {opportunity.relevance_score}</span>
                        <span>U: {opportunity.urgency_score}</span>
                        <span>V: {opportunity.value_score}</span>
                        <span>C: {opportunity.competition_score}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No opportunities found</h3>
                <p className="text-muted-foreground">
                  Try adjusting your search criteria or using different keywords
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

