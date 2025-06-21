# 📊 PostHog Analytics Setup Guide

## Overview

PostHog analytics is integrated into the Opportunity Dashboard to provide comprehensive insights into user behavior, feature usage, and application performance.

## 🚀 Quick Setup

### 1. **Create PostHog Account**
1. Go to [posthog.com](https://posthog.com)
2. Sign up for a free account
3. Create a new project for your Opportunity Dashboard

### 2. **Get Your API Keys**
- **Project API Key**: Found in Project Settings → API Keys
- **Personal API Key**: Found in Personal Settings → Personal API Keys

### 3. **Configure Environment Variables**

**Backend (.env):**
```bash
POSTHOG_API_KEY=phc_your_project_api_key_here
POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_ENABLED=true
```

**Frontend (.env.local):**
```bash
VITE_POSTHOG_KEY=phc_your_project_api_key_here  
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_POSTHOG_ENABLED=true
```

### 4. **Start Your Application**
```bash
# Backend
cd backend
python -m flask --app src.main run

# Frontend  
cd frontend
npm run dev
```

## 📈 **What Gets Tracked**

### **Frontend Events**
- **Page Views**: All route changes and page visits
- **User Authentication**: Login, logout, registration
- **Opportunity Interactions**: View, search, filter, status changes
- **Dashboard Usage**: Load times, refresh actions, chart interactions
- **Feature Usage**: Search, filters, sync, exports
- **Errors**: JavaScript errors with context
- **Performance**: Page load times, API response times

### **Backend Events**
- **API Requests**: Endpoint usage, response times, status codes
- **Opportunity Management**: CRUD operations, bulk operations
- **Data Synchronization**: Sync status, duration, records processed
- **Search Queries**: Search terms, filters, result counts
- **User Actions**: All authenticated user activities
- **Errors**: Server errors with stack traces
- **Performance Metrics**: Database query times, processing duration

## 🎯 **Key Metrics Tracked**

### **User Engagement**
- Daily/Monthly Active Users
- Session duration and frequency
- Page views and bounce rates
- Feature adoption rates

### **Application Performance**
- API response times
- Dashboard load performance
- Error rates and types
- Database query performance

### **Business Metrics**
- Opportunity views and searches
- Most popular agencies and sources
- User workflow patterns
- Feature usage statistics

## 📊 **Analytics Dashboard**

Access the analytics dashboard at `/analytics` to view:

- **User Activity**: Daily users, sessions, page views
- **Feature Usage**: Most used features and adoption rates
- **Top Pages**: Most visited pages and performance
- **Error Tracking**: Application errors and their impact
- **Performance Insights**: Load times and optimization opportunities

## 🔧 **Custom Event Tracking**

### **Frontend Custom Events**
```javascript
import { analytics } from '../lib/analytics'

// Track custom events
analytics.track('custom_event_name', {
  property1: 'value1',
  property2: 'value2'
})

// Track user properties
analytics.setUserProperties({
  plan: 'pro',
  company: 'Acme Corp'
})

// Track feature usage
analytics.trackFeatureUsage('advanced_search', 'used', {
  filters: ['agency', 'value'],
  results: 25
})
```

### **Backend Custom Events**
```python
from src.services.analytics_service import analytics_service

# Track custom events
analytics_service.track_custom_event('custom_event', {
    'property1': 'value1',
    'property2': 'value2'
}, user_id='user123')

# Track performance metrics
analytics_service.track_performance_metric('database_query_time', 150, {
    'query_type': 'opportunity_search',
    'results_count': 25
})
```

## 🔒 **Privacy & Compliance**

### **Data Collection**
- Only collects anonymized usage data
- No personal information stored in events
- IP addresses are hashed for privacy
- GDPR/CCPA compliant configuration

### **User Control**
- Analytics can be disabled per environment
- Users can opt-out via PostHog settings
- No tracking in development unless explicitly enabled

### **Security**
- API keys stored securely in environment variables
- Data transmitted over HTTPS
- Regular security updates from PostHog

## 🚀 **Production Deployment**

### **Railway (Backend)**
Add environment variables in Railway dashboard:
```bash
POSTHOG_API_KEY=phc_your_production_key
POSTHOG_HOST=https://us.i.posthog.com  
POSTHOG_ENABLED=true
```

### **Vercel (Frontend)**
Add environment variables in Vercel dashboard:
```bash
VITE_POSTHOG_KEY=phc_your_production_key
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_POSTHOG_ENABLED=true
```

## 📋 **Configuration Options**

### **PostHog Settings**
- **Session Recording**: Disabled by default for privacy
- **Feature Flags**: Enabled for A/B testing
- **Heatmaps**: Can be enabled for UX insights
- **Autocapture**: Limited to specific elements for performance

### **Custom Configuration**
```javascript
// Frontend: src/lib/analytics.js
posthog.init(apiKey, {
  api_host: 'https://us.i.posthog.com',
  person_profiles: 'identified_only',
  capture_pageview: true,
  capture_pageleave: true,
  // Add custom options here
})
```

## 🐛 **Troubleshooting**

### **Analytics Not Working**
1. Check environment variables are set correctly
2. Verify PostHog API key is valid
3. Check browser console for errors
4. Ensure POSTHOG_ENABLED=true

### **Events Not Appearing**
1. Check PostHog dashboard (events may take 1-2 minutes)
2. Verify network connectivity to PostHog
3. Check if ad blockers are interfering
4. Review browser dev tools network tab

### **Performance Issues**
1. PostHog events are sent asynchronously
2. Failed events are retried automatically
3. Consider reducing event frequency if needed
4. Monitor PostHog quota usage

## 📚 **Resources**

- **PostHog Documentation**: [posthog.com/docs](https://posthog.com/docs)
- **Analytics Dashboard**: `/analytics` (when enabled)
- **PostHog Dashboard**: [app.posthog.com](https://app.posthog.com)
- **API Reference**: [posthog.com/docs/api](https://posthog.com/docs/api)

## 🎯 **Best Practices**

1. **Event Naming**: Use clear, consistent event names
2. **Properties**: Include relevant context in event properties
3. **User Identification**: Identify users for better insights
4. **Privacy**: Never track sensitive information
5. **Performance**: Track events asynchronously
6. **Testing**: Test analytics in staging before production

---

**PostHog Analytics Integration Complete! 🎉**

Your Opportunity Dashboard now has comprehensive analytics tracking for better insights into user behavior and application performance. 