"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, ExternalLink, MessageSquare, Code2, Eye, Sparkles, RefreshCw, Heart, Lightbulb, Plus, Mic, Search, History, Square, Crown, Zap, Github, ArrowUp, Clock, Brain, Wrench, CheckCircle } from "lucide-react"
import { ModeToggle } from "@/components/ui/theme-toggle"

export default function ResultView() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session')
  const userMessage = searchParams.get('message')
  const selectedModel = searchParams.get('model') || 'k2' // Get model from URL params
  const [state, setState] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(true)
  const [newMessage, setNewMessage] = useState("")
  const [sendingMessage, setSendingMessage] = useState(false)
  const [loadingStage, setLoadingStage] = useState("Initializing...")
  
  // Use useRef to persist the initialization state across re-renders
  const hasInitializedRef = useRef(false)
  const loadingIntervalRef = useRef(null)

  // Loading stages animation
  const loadingStages = [
    "Initializing...",
    "Analyzing requirements...",
    "Generating code...",
    "Building application...",
    "Deploying to sandbox...",
    "Validating components...",
    "Finalizing setup..."
  ]

  // Start loading animation
  const startLoadingAnimation = () => {
    let stageIndex = 0
    setLoadingStage(loadingStages[0])
    
    loadingIntervalRef.current = setInterval(() => {
      stageIndex = (stageIndex + 1) % loadingStages.length
      setLoadingStage(loadingStages[stageIndex])
    }, 2000)
  }

  // Stop loading animation
  const stopLoadingAnimation = () => {
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current)
      loadingIntervalRef.current = null
    }
  }

  // Load initial data from backend - ONLY ONCE
  useEffect(() => {
    // CRITICAL FIX: Use ref to prevent multiple calls
    if (sessionId && !hasInitializedRef.current) {
      hasInitializedRef.current = true
      console.log(' INITIALIZING - Making ONE API call for session:', sessionId, 'with model:', selectedModel)
      
      // Show initial state immediately with user message
      setState({
        session_id: sessionId,
        context: {
          final_result: {
            success: false,
            url: null,
            message: "Generating your app...",
            validation_passed: false
          }
        },
        messages: [
          { 
            role: "user", 
            content: userMessage || "create a ui ux for spa website", 
            created_at: new Date().toISOString() 
          }
        ]
      })
      
      // Start loading animation
      startLoadingAnimation()
      
      // Make actual API call to backend - ONLY ONCE
      const makeInitialCall = async () => {
        try {
          const formData = new FormData()
          formData.append('text', userMessage || "create a ui ux for spa website")
          formData.append('session_id', sessionId)
          formData.append('llm_model', selectedModel) // Add model parameter

          console.log('📡 Making SINGLE API call to backend with model:', selectedModel)
          const response = await fetch('/api/query', {
            method: 'POST',
            body: formData
          })

          const result = await response.json()
          console.log(' Backend response received:', result)
          
          if (result.accepted && result.state) {
            console.log('✅ SUCCESS - Setting state with backend data')
            console.log('🔗 Final result URL:', result.state.context?.final_result?.url)
            
            // FIXED: Use backend messages directly - no test message, no overwriting
            setState(result.state)
            
            setPreviewLoading(false)
            stopLoadingAnimation()
            setLoadingStage("Complete!")
          } else {
            console.log('❌ Backend response not accepted:', result)
            setPreviewLoading(false)
            stopLoadingAnimation()
            setLoadingStage("Error occurred")
          }
        } catch (error) {
          console.error('❌ Error loading initial data:', error)
          setPreviewLoading(false)
          stopLoadingAnimation()
          setLoadingStage("Error occurred")
        }
      }

      makeInitialCall()
    } else if (sessionId && hasInitializedRef.current) {
      console.log(' PREVENTED - API call already made for session:', sessionId)
    }

    // Cleanup on unmount
    return () => {
      stopLoadingAnimation()
    }
  }, [sessionId, selectedModel]) // Added selectedModel to dependencies

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!newMessage.trim()) return

    // FIXED: Add user message immediately to UI
    const userMessageObj = {
      role: "user",
      content: newMessage,
      created_at: new Date().toISOString()
    }

    // Update state immediately with user message
    setState(prevState => ({
      ...prevState,
      messages: [...(prevState?.messages || []), userMessageObj]
    }))

    // Clear input immediately
    const messageToSend = newMessage
    setNewMessage("")
    setSendingMessage(true)
    
    try {
      const formData = new FormData()
      formData.append('text', messageToSend)
      formData.append('session_id', sessionId)
      formData.append('llm_model', selectedModel) // Add model parameter

      const response = await fetch('/api/query', {
        method: 'POST',
        body: formData
      })

      const result = await response.json()
      
      if (result.accepted && result.state) {
        // FIXED: Merge backend messages with existing frontend messages to preserve user messages
        const backendMessages = result.state.messages || []
        const currentMessages = state?.messages || []
        
        // Find messages that are in backend but not in current state (new AI responses)
        const newMessages = backendMessages.filter(backendMsg => 
          !currentMessages.some(currentMsg => 
            currentMsg.role === backendMsg.role && 
            currentMsg.content === backendMsg.content &&
            currentMsg.created_at === backendMsg.created_at
          )
        )
        
        // Update state with merged messages
        setState({
          ...result.state,
          messages: [...currentMessages, ...newMessages]
        })
        
        // FIXED: Check if new URL is available and update preview
        const newUrl = result.state.context?.final_result?.url
        if (newUrl && newUrl !== state?.context?.final_result?.url) {
          console.log('🔄 New URL detected, updating preview:', newUrl)
          setPreviewLoading(false) // Ensure preview is not loading if we have a URL
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setSendingMessage(false)
    }
  }

  const handleOpenExternal = () => {
    if (finalResult?.url) {
      window.open(finalResult.url, '_blank', 'noopener,noreferrer')
    }
  }

  const finalResult = state?.context?.final_result
  const messages = state?.messages || []

  // Enhanced debug logging
  console.log('🔍 Current state:', state)
  console.log('🔍 Final result:', finalResult)
  console.log('🔍 Messages array:', messages)
  console.log(' Messages length:', messages.length)
  if (messages.length > 0) {
    console.log(' First message:', messages[0])
    console.log(' All messages:', messages.map((msg, i) => ({ 
      index: i, 
      role: msg.role, 
      content: msg.content?.substring(0, 100) + '...',
      created_at: msg.created_at 
    })))
  }
  console.log(' Preview loading:', previewLoading)
  console.log(' Has initialized:', hasInitializedRef.current)
  console.log('🔍 Selected model:', selectedModel)

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Top Header Bar */}
      <div className="bg-background px-4 py-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
                <span className="text-xs font-bold text-primary-foreground">S</span>
              </div>
              <span className="text-sm font-medium text-foreground">spa-sparkle-studio</span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {finalResult?.url && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleOpenExternal}
                className="text-muted-foreground hover:text-foreground"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            )}
            <ModeToggle />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* Chat Panel - Left Side */}
          <ResizablePanel defaultSize={30} minSize={20}>
            <div className="h-full flex flex-col bg-card">
              {/* Messages - FIXED: Only messages area scrolls, not entire UI */}
              <div className="flex-1 min-h-0">
                <ScrollArea className="h-full p-4">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-lg p-3 ${
                            message.role === 'user'
                              ? 'bg-primary text-primary-foreground ml-4'
                              : 'bg-muted text-muted-foreground mr-4'
                          }`}
                        >
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">
                            {message.content}
                          </div>
                          <div className="text-xs opacity-70 mt-2 flex items-center gap-1">
                            {message.role === 'assistant' && (
                              <>
                                <Heart className="h-3 w-3 text-destructive" />
                                <span>Growth-AI</span>
                                <span>•</span>
                              </>
                            )}
                            <span>{new Date(message.created_at).toLocaleTimeString()}</span>
                            {message.role === 'assistant' && (
                              <>
                                <span>•</span>
                                <span>Thought for 10 seconds</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {/* Thinking indicator */}
                    {(previewLoading || sendingMessage) && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Heart className="h-4 w-4 text-destructive" />
                        <span className="text-sm">Growth-AI</span>
                        <Lightbulb className="h-4 w-4" />
                        <span className="text-sm">Thinking</span>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </div>

              {/* Input - Fixed at bottom */}
              <div className="flex-shrink-0 p-4">
                <form onSubmit={handleSendMessage}>
                  <div className="relative">
                    <Textarea
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Ask Growth-AI..."
                      className="min-h-[100px] resize-none bg-background border-border text-foreground placeholder-muted-foreground pr-12 rounded-xl focus:ring-2 focus:ring-ring focus:border-transparent shadow-2xl shadow-primary/20 hover:shadow-[0_0_30px_rgba(217,119,87,0.4)] hover:border-[#d97757] transition-all duration-300"
                      disabled={sendingMessage}
                    />
                    <div className="absolute right-2 bottom-2 flex items-center gap-2">
                      <Button 
                      type="button" 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground cursor-pointer rounded-full"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button 
                        type="submit" 
                        size="icon"
                        className="h-6 w-6 p-0 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full cursor-pointer"
                        disabled={sendingMessage || !newMessage.trim()}
                      >
                        {sendingMessage ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <ArrowUp className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="md:hidden" />

          {/* Preview Panel - Right Side */}
          <ResizablePanel defaultSize={70} minSize={40}>
            <div className="h-full flex flex-col bg-background ">
              <div className="flex-1 p-1">
                {previewLoading ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-6">
                      {/* Animated loading icon */}
                      <div className="relative">
                        <Heart className="h-16 w-16 mx-auto text-muted-foreground animate-pulse" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Loader2 className="h-8 w-8 text-primary animate-spin" />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <h2 className="text-xl font-semibold text-foreground">Building your app...</h2>
                        <p className="text-sm text-muted-foreground">{loadingStage}</p>
                      </div>
                      
                      {/* Progress indicators */}
                      <div className="space-y-3 text-left max-w-sm">
                        <div className="flex items-center gap-3 text-sm">
                          <div className="w-4 h-4 border border-border rounded flex items-center justify-center">
                            {loadingStage.includes('Analyzing') && <Brain className="h-2 w-2 text-primary animate-pulse" />}
                            {loadingStage.includes('Generating') && <Code2 className="h-2 w-2 text-primary animate-pulse" />}
                            {loadingStage.includes('Building') && <Wrench className="h-2 w-2 text-primary animate-pulse" />}
                            {loadingStage.includes('Deploying') && <Zap className="h-2 w-2 text-primary animate-pulse" />}
                            {loadingStage.includes('Validating') && <CheckCircle className="h-2 w-2 text-primary animate-pulse" />}
                          </div>
                          <span>Select specific elements to modify</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <div className="w-4 h-4 border border-border rounded"></div>
                          <span>Upload images as a reference</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <div className="w-4 h-4 border border-border rounded"></div>
                          <span>Instantly preview your changes</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm opacity-50">
                          <div className="w-4 h-4 border border-border rounded"></div>
                          <span>Set custom knowledge for every edit</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : finalResult?.url ? (
                  <div className="h-full">
                    <iframe
                      key={finalResult.url} // FIXED: Force iframe reload when URL changes
                      src={finalResult.url}
                      className="w-full h-full rounded-lg border border-border shadow-sm"
                      title="App Preview"
                    />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-2">
                      <Code2 className="h-12 w-12 mx-auto" />
                      <p>Preview will appear here once your app is ready</p>
                      {finalResult && (
                        <div className="text-xs text-destructive mt-2">
                          Status: {finalResult.message || 'Unknown status'}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </div>
  )
}
