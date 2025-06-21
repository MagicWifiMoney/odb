import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  FileText, 
  Search, 
  Settings, 
  RefreshCw, 
  Menu, 
  X,
  Moon,
  Sun,
  Target,
  TrendingUp,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Opportunities', href: '/opportunities', icon: FileText },
  { name: 'Search', href: '/search', icon: Search },
  { name: 'Perplexity', href: '/perplexity', icon: Zap },
  { name: 'Sync Status', href: '/sync', icon: RefreshCw },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar({ isOpen, onToggle, darkMode, onToggleDarkMode }) {
  const location = useLocation()

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed top-0 left-0 z-50 h-full bg-sidebar border-r border-sidebar-border transition-all duration-300",
        isOpen ? "w-64" : "w-16"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
            <div className={cn(
              "flex items-center space-x-3 transition-opacity duration-300",
              isOpen ? "opacity-100" : "opacity-0"
            )}>
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <Target className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-sidebar-foreground">
                  OpportunityHub
                </h1>
                <p className="text-xs text-sidebar-foreground/60">
                  RFP & Grant Tracker
                </p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="text-sidebar-foreground hover:bg-sidebar-accent"
            >
              {isOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors duration-200",
                    isActive 
                      ? "bg-sidebar-accent text-sidebar-accent-foreground" 
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  )}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span className={cn(
                    "transition-opacity duration-300",
                    isOpen ? "opacity-100" : "opacity-0"
                  )}>
                    {item.name}
                  </span>
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-sidebar-border">
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleDarkMode}
              className={cn(
                "w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent",
                !isOpen && "justify-center"
              )}
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              <span className={cn(
                "ml-3 transition-opacity duration-300",
                isOpen ? "opacity-100" : "opacity-0"
              )}>
                {darkMode ? 'Light Mode' : 'Dark Mode'}
              </span>
            </Button>
            
            {isOpen && (
              <div className="mt-4 pt-4 border-t border-sidebar-border">
                <div className="flex items-center space-x-2 text-xs text-sidebar-foreground/60">
                  <TrendingUp className="w-3 h-3" />
                  <span>v1.0.0</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

