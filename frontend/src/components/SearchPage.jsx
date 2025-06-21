import { useState } from 'react'
import { Search, Filter, Calendar, DollarSign, Target } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { apiClient, formatCurrency, formatDate, formatRelativeDate, getScoreColor, getScoreBadgeColor, getUrgencyColor, getSourceTypeLabel, getSourceTypeColor } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function SearchPage() {
  const [searchForm, setSearchForm] = useState({
    keywords: '',
    agency_name: '',
    min_score: [0],
    max_value: '',
    min_value: '',
    due_within_days: 'any',
    source_type: 'all',
    location: '',
    category: 'all'
  })
  
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const { toast } = useToast()

  const handleInputChange = (field, value) => {
    setSearchForm(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSearch = async () => {
    try {
      setLoading(true)
      setHasSearched(true)
      
      // Prepare search data
      const searchData = {
        keywords: searchForm.keywords.split(',').map(k => k.trim()).filter(k => k),
        min_score: searchForm.min_score[0],
        due_within_days: searchForm.due_within_days !== 'any' ? parseInt(searchForm.due_within_days) : undefined,
        source_type: searchForm.source_type !== 'all' ? searchForm.source_type : undefined,
        agency_name: searchForm.agency_name || undefined,
        location: searchForm.location || undefined,
        category: searchForm.category !== 'all' ? searchForm.category : undefined,
        min_value: searchForm.min_value ? parseFloat(searchForm.min_value) : undefined,
        max_value: searchForm.max_value ? parseFloat(searchForm.max_value) : undefined
      }

      // Remove undefined values
      Object.keys(searchData).forEach(key => {
        if (searchData[key] === undefined || searchData[key] === '') {
          delete searchData[key]
        }
      })

      const data = await apiClient.searchOpportunities(searchData)
      setResults(data.opportunities || [])
      
      toast({
        title: "Search Complete",
        description: `Found ${data.opportunities?.length || 0} opportunities`,
      })
    } catch (error) {
      console.error('Search failed:', error)
      toast({
        title: "Search Failed",
        description: error.message || "Failed to search opportunities",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const clearSearch = () => {
    setSearchForm({
      keywords: '',
      agency_name: '',
      min_score: [0],
      max_value: '',
      min_value: '',
      due_within_days: 'any',
      source_type: 'all',
      location: '',
      category: 'all'
    })
    setResults([])
    setHasSearched(false)
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
                <Label htmlFor="agency">Agency Name</Label>
                <Input
                  id="agency"
                  placeholder="Department of Defense, NASA, etc."
                  value={searchForm.agency_name}
                  onChange={(e) => handleInputChange('agency_name', e.target.value)}
                />
              </div>
            </div>

            {/* Score and Value Filters */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Minimum Score: {searchForm.min_score[0]}</Label>
                <Slider
                  value={searchForm.min_score}
                  onValueChange={(value) => handleInputChange('min_score', value)}
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
                <Label htmlFor="min_value">Minimum Value ($)</Label>
                <Input
                  id="min_value"
                  type="number"
                  placeholder="10000"
                  value={searchForm.min_value}
                  onChange={(e) => handleInputChange('min_value', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_value">Maximum Value ($)</Label>
                <Input
                  id="max_value"
                  type="number"
                  placeholder="1000000"
                  value={searchForm.max_value}
                  onChange={(e) => handleInputChange('max_value', e.target.value)}
                />
              </div>
            </div>

            {/* Category and Source Filters */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label>Due Within (Days)</Label>
                <Select 
                  value={searchForm.due_within_days} 
                  onValueChange={(value) => handleInputChange('due_within_days', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Any time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any time</SelectItem>
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="14">14 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="60">60 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Source Type</Label>
                <Select 
                  value={searchForm.source_type} 
                  onValueChange={(value) => handleInputChange('source_type', value)}
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

              <div className="space-y-2">
                <Label>Category</Label>
                <Select 
                  value={searchForm.category} 
                  onValueChange={(value) => handleInputChange('category', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="construction">Construction</SelectItem>
                    <SelectItem value="services">Services</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="research">Research</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Location */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  placeholder="California, Washington DC, etc."
                  value={searchForm.location}
                  onChange={(e) => handleInputChange('location', e.target.value)}
                />
              </div>
            </div>

            <Separator />

            {/* Action Buttons */}
            <div className="flex items-center space-x-4">
              <Button onClick={handleSearch} disabled={loading}>
                <Search className="w-4 h-4 mr-2" />
                {loading ? 'Searching...' : 'Search Opportunities'}
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
              {loading ? 'Searching...' : `Found ${results.length} opportunities`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
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
            ) : results.length > 0 ? (
              <div className="space-y-4">
                {results.map((opportunity) => (
                  <div key={opportunity.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-semibold">{opportunity.title}</h3>
                      <Badge className={getScoreBadgeColor(opportunity.total_score)}>
                        <Target className="w-3 h-3 mr-1" />
                        {opportunity.total_score}
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
                        {opportunity.keywords && opportunity.keywords.slice(0, 3).map((keyword, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {opportunity.keywords && opportunity.keywords.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{opportunity.keywords.length - 3} more
                          </Badge>
                        )}
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

