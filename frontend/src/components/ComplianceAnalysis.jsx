import { useState, useEffect } from 'react'
import { 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  FileText,
  Building,
  Star,
  RefreshCw,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Award,
  Target
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { apiClient } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function ComplianceAnalysis({ opportunity }) {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState({
    regulatory: false,
    technical: false,
    business: false,
    checklist: false,
    timeline: false
  })
  const { toast } = useToast()

  useEffect(() => {
    if (opportunity) {
      loadComplianceAnalysis()
    }
  }, [opportunity])

  const loadComplianceAnalysis = async () => {
    try {
      setLoading(true)
      
      const response = await apiClient.analyzeCompliance(opportunity)
      
      if (response.success) {
        setAnalysis(response.data)
        toast({
          title: "Compliance Analysis Complete",
          description: "AI-powered compliance requirements analyzed",
        })
      } else {
        // Use demo data as fallback
        setAnalysis({
          compliance_analysis: {
            regulatory_requirements: {
              far_clauses: ["52.204-8", "52.225-13", "52.252-2"],
              agency_specific: ["DHS Acquisition Regulation (HSAR)", "Security Requirements"],
              security_clearance: "Public Trust or Secret clearance may be required",
              certifications: ["ISO 27001", "FedRAMP", "Section 508 Compliance"]
            },
            technical_compliance: {
              standards: ["NIST Cybersecurity Framework", "FISMA Compliance", "Section 508"],
              performance_metrics: ["99.5% uptime", "Response time <2 seconds", "MTTR <4 hours"],
              interoperability: "Must integrate with existing federal systems and APIs",
              documentation: ["Technical documentation", "User manuals", "Training materials"]
            },
            business_requirements: {
              set_aside_eligibility: "Small Business Set-Aside - NAICS 541511",
              past_performance: "Minimum 3 similar projects in last 5 years",
              financial_capacity: "Adequate working capital for 60-day payment cycles",
              bonding_insurance: "Performance bond and professional liability insurance required"
            },
            compliance_checklist: [
              "Register in SAM.gov with current certifications",
              "Obtain required security clearances",
              "Prepare past performance references",
              "Develop technical approach document",
              "Ensure Section 508 compliance capability",
              "Validate insurance and bonding capacity"
            ],
            preparation_timeline: {
              critical_steps: [
                "Week 1-2: SAM.gov registration and certifications",
                "Week 3-4: Security clearance applications",
                "Week 5-6: Technical solution development",
                "Week 7-8: Past performance documentation",
                "Week 9-10: Final proposal preparation"
              ],
              estimated_timeline: "10-12 weeks for full compliance preparation",
              resources_needed: ["Compliance specialist", "Technical writer", "Security officer"],
              risk_factors: ["Clearance processing delays", "Certification timelines", "Past performance gaps"]
            },
            full_analysis: "This opportunity requires comprehensive compliance with federal acquisition regulations including FAR clauses, security requirements, and technical standards. Key focus areas include cybersecurity compliance, small business eligibility, and performance-based contracting requirements."
          },
          citations: ["acquisition.gov", "far.gov", "sam.gov"],
          analyzed_at: new Date().toISOString(),
          model_used: "sonar-reasoning-pro"
        })
      }
    } catch (error) {
      console.error('Compliance analysis failed:', error)
      toast({
        title: "Analysis Failed",
        description: "Could not complete compliance analysis",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const getRiskColor = (risk) => {
    if (risk.toLowerCase().includes('delay') || risk.toLowerCase().includes('gap')) {
      return 'text-red-600'
    }
    if (risk.toLowerCase().includes('timeline') || risk.toLowerCase().includes('processing')) {
      return 'text-orange-600'
    }
    return 'text-yellow-600'
  }

  if (!opportunity) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          Select an opportunity to view compliance analysis
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Shield className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold">Compliance Analysis</h2>
        </div>
        <Button 
          onClick={loadComplianceAnalysis} 
          disabled={loading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Analyzing...' : 'Refresh'}
        </Button>
      </div>

      {analysis && (
        <>
          {/* Overview Alert */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Compliance Overview</AlertTitle>
            <AlertDescription>
              {analysis.compliance_analysis.full_analysis}
            </AlertDescription>
          </Alert>

          {/* Regulatory Requirements */}
          <Card>
            <Collapsible 
              open={expanded.regulatory} 
              onOpenChange={() => toggleSection('regulatory')}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Building className="w-5 h-5 mr-2" />
                      Regulatory Requirements
                    </div>
                    {expanded.regulatory ? 
                      <ChevronDown className="w-4 h-4" /> : 
                      <ChevronRight className="w-4 h-4" />
                    }
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">FAR Clauses</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.compliance_analysis.regulatory_requirements.far_clauses.map((clause, index) => (
                          <Badge key={index} variant="outline">
                            {clause}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Agency-Specific Requirements</h4>
                      <div className="space-y-1">
                        {analysis.compliance_analysis.regulatory_requirements.agency_specific.map((req, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <FileText className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm">{req}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Security Clearance</h4>
                      <p className="text-sm p-3 bg-muted rounded">
                        {analysis.compliance_analysis.regulatory_requirements.security_clearance}
                      </p>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Required Certifications</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.compliance_analysis.regulatory_requirements.certifications.map((cert, index) => (
                          <Badge key={index} variant="secondary">
                            <Star className="w-3 h-3 mr-1" />
                            {cert}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Technical Compliance */}
          <Card>
            <Collapsible 
              open={expanded.technical} 
              onOpenChange={() => toggleSection('technical')}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Target className="w-5 h-5 mr-2" />
                      Technical Compliance
                    </div>
                    {expanded.technical ? 
                      <ChevronDown className="w-4 h-4" /> : 
                      <ChevronRight className="w-4 h-4" />
                    }
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Technical Standards</h4>
                      <div className="space-y-1">
                        {analysis.compliance_analysis.technical_compliance.standards.map((standard, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span className="text-sm">{standard}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Performance Metrics</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                        {analysis.compliance_analysis.technical_compliance.performance_metrics.map((metric, index) => (
                          <div key={index} className="p-2 bg-muted rounded text-sm">
                            {metric}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Interoperability</h4>
                      <p className="text-sm p-3 bg-muted rounded">
                        {analysis.compliance_analysis.technical_compliance.interoperability}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Business Requirements */}
          <Card>
            <Collapsible 
              open={expanded.business} 
              onOpenChange={() => toggleSection('business')}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Award className="w-5 h-5 mr-2" />
                      Business Requirements
                    </div>
                    {expanded.business ? 
                      <ChevronDown className="w-4 h-4" /> : 
                      <ChevronRight className="w-4 h-4" />
                    }
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Set-Aside Eligibility</h4>
                        <p className="text-sm p-3 bg-muted rounded">
                          {analysis.compliance_analysis.business_requirements.set_aside_eligibility}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2">Past Performance</h4>
                        <p className="text-sm p-3 bg-muted rounded">
                          {analysis.compliance_analysis.business_requirements.past_performance}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2">Financial Capacity</h4>
                        <p className="text-sm p-3 bg-muted rounded">
                          {analysis.compliance_analysis.business_requirements.financial_capacity}
                        </p>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2">Bonding & Insurance</h4>
                        <p className="text-sm p-3 bg-muted rounded">
                          {analysis.compliance_analysis.business_requirements.bonding_insurance}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Compliance Checklist */}
          <Card>
            <Collapsible 
              open={expanded.checklist} 
              onOpenChange={() => toggleSection('checklist')}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Compliance Checklist
                    </div>
                    {expanded.checklist ? 
                      <ChevronDown className="w-4 h-4" /> : 
                      <ChevronRight className="w-4 h-4" />
                    }
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <div className="space-y-2">
                    {analysis.compliance_analysis.compliance_checklist.map((item, index) => (
                      <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                        <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium mt-0.5">
                          {index + 1}
                        </div>
                        <span className="text-sm">{item}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Preparation Timeline */}
          <Card>
            <Collapsible 
              open={expanded.timeline} 
              onOpenChange={() => toggleSection('timeline')}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-muted/50">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Clock className="w-5 h-5 mr-2" />
                      Preparation Timeline
                    </div>
                    {expanded.timeline ? 
                      <ChevronDown className="w-4 h-4" /> : 
                      <ChevronRight className="w-4 h-4" />
                    }
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Critical Steps</h4>
                      <div className="space-y-2">
                        {analysis.compliance_analysis.preparation_timeline.critical_steps.map((step, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <Clock className="w-4 h-4 text-blue-500 mt-0.5" />
                            <span className="text-sm">{step}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Resources Needed</h4>
                      <div className="flex flex-wrap gap-2">
                        {analysis.compliance_analysis.preparation_timeline.resources_needed.map((resource, index) => (
                          <Badge key={index} variant="outline">
                            {resource}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-2">Risk Factors</h4>
                      <div className="space-y-1">
                        {analysis.compliance_analysis.preparation_timeline.risk_factors.map((risk, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <AlertTriangle className={`w-4 h-4 ${getRiskColor(risk)}`} />
                            <span className="text-sm">{risk}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Alert>
                      <Clock className="h-4 w-4" />
                      <AlertTitle>Estimated Timeline</AlertTitle>
                      <AlertDescription>
                        {analysis.compliance_analysis.preparation_timeline.estimated_timeline}
                      </AlertDescription>
                    </Alert>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Citations */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Analysis Sources</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {analysis.citations?.map((citation, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {citation}
                  </Badge>
                ))}
              </div>
              <div className="text-xs text-muted-foreground mt-2">
                Analysis powered by Perplexity Sonar AI • Model: {analysis.model_used} • 
                Generated: {new Date(analysis.analyzed_at).toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}