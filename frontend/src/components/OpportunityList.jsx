import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search, 
  Filter, 
  SortAsc, 
  SortDesc, 
  ExternalLink,
  Calendar,
  DollarSign,
  Building,
  Target
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { formatCurrency, formatDate, formatRelativeDate, getScoreColor, getScoreBadgeColor, getUrgencyColor, getSourceTypeLabel, getSourceTypeColor } from '../lib/api'
import { useToast } from '../hooks/use-toast'
import { supabase } from '../lib/supabase'

export default function OpportunityList() {
  const [opportunities, setOpportunities] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('total_score')
  const [sortOrder, setSortOrder] = useState('desc')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 50, // Increased for better performance with large datasets
    total: 0,
    pages: 0
  })
  const { toast } = useToast()

  useEffect(() => {
    // Debounce search to avoid too many API calls
    const timeoutId = setTimeout(() => {
      loadOpportunities()
    }, searchTerm ? 300 : 0) // 300ms delay for search, immediate for other filters
    
    return () => clearTimeout(timeoutId)
  }, [searchTerm, sortBy, sortOrder, statusFilter, sourceFilter, pagination.page]) // eslint-disable-line react-hooks/exhaustive-deps

  const loadOpportunities = async () => {
    try {
      setLoading(true)
      
      console.log('Loading opportunities from Supabase...')
      const startTime = performance.now()
      
      // Build Supabase query
      let query = supabase
        .from('opportunities')
        .select('*', { count: 'exact' })

      // Apply search filter
      if (searchTerm) {
        query = query.or(`title.ilike.%${searchTerm}%,description.ilike.%${searchTerm}%,agency_name.ilike.%${searchTerm}%`)
      }

      // Apply status filter (if your database has a status field)
      if (statusFilter !== 'all') {
        query = query.eq('status', statusFilter)
      }

      // Apply source type filter
      if (sourceFilter !== 'all') {
        query = query.eq('source_type', sourceFilter)
      }

      // Apply sorting
      const sortField = sortBy === 'total_score' ? 'relevance_score' : sortBy
      query = query.order(sortField, { ascending: sortOrder === 'asc' })

      // Apply pagination
      const from = (pagination.page - 1) * pagination.per_page
      const to = from + pagination.per_page - 1
      query = query.range(from, to)

      const { data, error, count } = await query

      if (error) throw error
      
      const endTime = performance.now()
      console.log(`Opportunities loaded in ${endTime - startTime}ms`)
      
      setOpportunities(data || [])
      setPagination({
        ...pagination,
        total: count || 0,
        pages: Math.ceil((count || 0) / pagination.per_page)
      })
    } catch (error) {
      console.error('Failed to load opportunities:', error)
      toast({
        title: "Error",
        description: `Failed to load opportunities: ${error.message}`,
        variant: "destructive",
      })
      // Set empty state on error
      setOpportunities([])
      setPagination({
        ...pagination,
        total: 0,
        pages: 0
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    setSearchTerm(e.target.value)
    setPagination({ ...pagination, page: 1 })
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setPagination({ ...pagination, page: 1 })
  }

  const handlePageChange = (newPage) => {
    setPagination({ ...pagination, page: newPage })
  }

  const SortButton = ({ field, children }) => (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => handleSort(field)}
      className="h-auto p-1 font-medium"
    >
      {children}
      {sortBy === field && (
        sortOrder === 'asc' ? <SortAsc className="w-3 h-3 ml-1" /> : <SortDesc className="w-3 h-3 ml-1" />
      )}
    </Button>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Opportunities</h1>
          <p className="text-muted-foreground">
            Browse and filter RFP and grant opportunities
          </p>
        </div>
        <Link to="/search">
          <Button>
            <Search className="w-4 h-4 mr-2" />
            Advanced Search
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search opportunities..."
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                  <SelectItem value="upcoming">Upcoming</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Source Type</label>
              <Select value={sourceFilter} onValueChange={setSourceFilter}>
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
              <label className="text-sm font-medium">Sort By</label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="total_score">Score</SelectItem>
                  <SelectItem value="due_date">Due Date</SelectItem>
                  <SelectItem value="estimated_value">Value</SelectItem>
                  <SelectItem value="posted_date">Posted Date</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {opportunities.length} of {pagination.total} opportunities
        </p>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page <= 1}
          >
            Previous
          </Button>
          <span className="text-sm">
            Page {pagination.page} of {pagination.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
          >
            Next
          </Button>
        </div>
      </div>

      {/* Opportunities List */}
      <div className="space-y-4">
        {loading ? (
          // Loading skeleton
          [...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="space-y-3">
                  <div className="h-6 bg-muted animate-pulse rounded"></div>
                  <div className="h-4 bg-muted animate-pulse rounded w-3/4"></div>
                  <div className="flex space-x-2">
                    <div className="h-6 bg-muted animate-pulse rounded w-16"></div>
                    <div className="h-6 bg-muted animate-pulse rounded w-20"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : opportunities.length > 0 ? (
          opportunities.map((opportunity) => (
            <Card key={opportunity.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <Link 
                        to={`/opportunities/${opportunity.id}`}
                        className="text-lg font-semibold hover:text-primary transition-colors"
                      >
                        {opportunity.title}
                      </Link>
                      <div className="flex items-center space-x-2 ml-4">
                        <Badge className={getScoreBadgeColor(opportunity.total_score)}>
                          <Target className="w-3 h-3 mr-1" />
                          {opportunity.total_score}
                        </Badge>
                        {opportunity.source_url && (
                          <Button variant="ghost" size="sm" asChild>
                            <a href={opportunity.source_url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          </Button>
                        )}
                      </div>
                    </div>

                    <p className="text-muted-foreground mb-3 line-clamp-2">
                      {opportunity.description || 'No description available'}
                    </p>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="flex items-center space-x-2">
                        <Building className="w-4 h-4 text-muted-foreground" />
                        <div>
                          <p className="text-xs text-muted-foreground">Agency</p>
                          <p className="text-sm font-medium truncate">
                            {opportunity.agency_name || 'Unknown'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <DollarSign className="w-4 h-4 text-muted-foreground" />
                        <div>
                          <p className="text-xs text-muted-foreground">Value</p>
                          <p className="text-sm font-medium">
                            {opportunity.estimated_value ? formatCurrency(opportunity.estimated_value) : 'N/A'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Calendar className="w-4 h-4 text-muted-foreground" />
                        <div>
                          <p className="text-xs text-muted-foreground">Due Date</p>
                          <p className={`text-sm font-medium ${getUrgencyColor(opportunity.due_date)}`}>
                            {opportunity.due_date ? formatRelativeDate(opportunity.due_date) : 'N/A'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Posted</p>
                          <p className="text-sm font-medium">
                            {opportunity.posted_date ? formatDate(opportunity.posted_date) : 'N/A'}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className={getSourceTypeColor(opportunity.source_type)}>
                          {getSourceTypeLabel(opportunity.source_type)}
                        </Badge>
                        <Badge variant="secondary">
                          {opportunity.source_name}
                        </Badge>
                        {opportunity.opportunity_number && (
                          <Badge variant="outline">
                            {opportunity.opportunity_number}
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>Relevance: {opportunity.relevance_score}</span>
                        <span>Urgency: {opportunity.urgency_score}</span>
                        <span>Value: {opportunity.value_score}</span>
                        <span>Competition: {opportunity.competition_score}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No opportunities found</h3>
              <p className="text-muted-foreground mb-4">
                Try adjusting your filters or search terms
              </p>
              <Button onClick={() => {
                setSearchTerm('')
                setStatusFilter('all')
                setSourceFilter('all')
                setPagination({ ...pagination, page: 1 })
              }}>
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <Button
            variant="outline"
            onClick={() => handlePageChange(1)}
            disabled={pagination.page <= 1}
          >
            First
          </Button>
          <Button
            variant="outline"
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page <= 1}
          >
            Previous
          </Button>
          
          {/* Page numbers */}
          {[...Array(Math.min(5, pagination.pages))].map((_, i) => {
            const pageNum = Math.max(1, pagination.page - 2) + i
            if (pageNum <= pagination.pages) {
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === pagination.page ? "default" : "outline"}
                  onClick={() => handlePageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              )
            }
            return null
          })}
          
          <Button
            variant="outline"
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
          >
            Next
          </Button>
          <Button
            variant="outline"
            onClick={() => handlePageChange(pagination.pages)}
            disabled={pagination.page >= pagination.pages}
          >
            Last
          </Button>
        </div>
      )}
    </div>
  )
}

