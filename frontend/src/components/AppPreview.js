"use client"

import { useState, useEffect } from "react"
import { Loader2, Brain, Code2, Search, FileText, CheckCircle, Sparkles, Zap, Globe, Layers } from "lucide-react"
import Image from "next/image"

export default function AppPreview({ 
  previewLoading, 
  loadingStage, 
  sandboxUrl, 
  selectedMessageId 
}) {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  const loadingSteps = [
    {
      icon: Brain,
      title: "Analyzing Request",
      description: "Understanding your requirements and planning the approach",
      color: "text-blue-500"
    },
    {
      icon: Search,
      title: "Generating Code",
      description: "Creating the application structure and components",
      color: "text-purple-500"
    },
    {
      icon: FileText,
      title: "Building Assets",
      description: "Compiling styles, scripts, and resources",
      color: "text-green-500"
    },
    {
      icon: Globe,
      title: "Deploying Preview",
      description: "Setting up the live preview environment",
      color: "text-orange-500"
    },
    {
      icon: CheckCircle,
      title: "Finalizing",
      description: "Completing the build and preparing for launch",
      color: "text-emerald-500"
    }
  ]

  useEffect(() => {
    if (previewLoading) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            return 100
          }
          return prev + Math.random() * 12
        })
      }, 600)

      const stepInterval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= loadingSteps.length - 1) {
            clearInterval(stepInterval)
            return loadingSteps.length - 1
          }
          return prev + 1
        })
      }, 1800)

      return () => {
        clearInterval(interval)
        clearInterval(stepInterval)
      }
    } else {
      setProgress(0)
      setCurrentStep(0)
    }
  }, [previewLoading])

  if (previewLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-background border border-border rounded-xl">
        <div className="w-full max-w-xl mx-auto px-6">
          {/* Main Loading Animation */}
          <div className="text-center space-y-6 mb-6">
            <div className="relative">
              <div className="w-20 h-20 mx-auto relative">
                {/* Outer rotating ring */}
                <div className="absolute inset-0 rounded-full border-3 border-primary/10"></div>
                <div className="absolute inset-0 rounded-full border-3 border-transparent border-t-primary animate-spin"></div>
                
                {/* Inner pulsing circle */}
                <div className="absolute inset-3 rounded-full bg-primary/5 flex items-center justify-center">
                  <Image src="/logo.png" alt="Logo" width={30} height={30} />
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-foreground">
                Building Your Application
              </h2>
              <p className="text-muted-foreground text-sm">
                {loadingStage || "Crafting something amazing for you..."}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-muted/50 rounded-full h-1.5 mb-6 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary to-primary/80 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          {/* Loading Steps */}
          <div className="space-y-3">
            {loadingSteps.map((step, index) => {
              const Icon = step.icon
              const isActive = index === currentStep
              const isCompleted = index < currentStep
              const isUpcoming = index > currentStep

              return (
                <div
                  key={index}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-400 ${
                    isActive 
                      ? 'bg-primary/8 border border-primary/15 shadow-sm' 
                      : isCompleted 
                        ? 'bg-emerald-50/50 dark:bg-emerald-950/10 border border-emerald-200/50 dark:border-emerald-800/30' 
                        : 'bg-muted/30 border border-border/30'
                  }`}
                >
                  {/* Step Icon */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : isCompleted 
                        ? 'bg-emerald-500 text-white' 
                        : 'bg-muted text-muted-foreground'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <Icon className={`h-4 w-4 ${isActive ? 'animate-pulse' : ''}`} />
                    )}
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className={`text-sm font-medium transition-colors duration-300 ${
                      isActive 
                        ? 'text-primary' 
                        : isCompleted 
                          ? 'text-emerald-700 dark:text-emerald-300' 
                          : 'text-muted-foreground'
                    }`}>
                      {step.title}
                    </h3>
                    <p className={`text-xs transition-colors duration-300 ${
                      isActive 
                        ? 'text-foreground/80' 
                        : isCompleted 
                          ? 'text-emerald-600/80 dark:text-emerald-400/80' 
                          : 'text-muted-foreground/70'
                    }`}>
                      {step.description}
                    </p>
                  </div>

                  {/* Loading indicator for active step */}
                  {isActive && (
                    <div className="flex-shrink-0">
                      <Loader2 className="h-4 w-4 text-primary animate-spin" />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Additional Info */}
          <div className="mt-6 text-center">
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Layers className="h-3 w-3" />
              <span>Powered by Growth-AI • Advanced Code Generation</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (sandboxUrl) {
    return (
      <div className="h-full relative bg-background">
        <iframe
          key={`${selectedMessageId}-${sandboxUrl}`}
          src={sandboxUrl}
          className="w-full h-full rounded-lg border border-border shadow-sm"
          title="App Preview"
          loading="lazy"
        />
      </div>
    )
  }

  return (
    <div className="h-full flex items-center justify-center bg-background">
      <div className="text-center space-y-4 max-w-sm mx-auto px-6">
        <div className="relative">
          <div className="w-16 h-16 mx-auto relative">
            <div className="absolute inset-0 rounded-full bg-primary/8 flex items-center justify-center">
              <Code2 className="h-8 w-8 text-primary/60" />
            </div>
            <div className="absolute inset-0 rounded-full border-2 border-dashed border-primary/20 animate-pulse"></div>
          </div>
        </div>
        
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">
            Ready to Build
          </h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Your generated application will appear here once the backend processing is complete.
          </p>
        </div>
        
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span>AI-powered development in progress</span>
        </div>
      </div>
    </div>
  )
}
