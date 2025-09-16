"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, RefreshCw, Heart, Lightbulb, ArrowUp, Brain, Code2, ExternalLink, Image, Upload, Download, Plus, FileText, ImagePlus } from "lucide-react"
import { authClient } from "@/lib/auth-client"
import SignInForm from "@/app/(auth)/sign-in/sign-in-form"
import { ModeToggle } from "@/components/ui/theme-toggle"
import { 
  createConversation, 
  addMessage, 
  updateAssistantMessage, 
  getConversation 
} from '@/lib/actions/conversation-actions'
import GitHubDeploy from "./GithubDeploy.jsx"

export default function ResultView() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session')
  const initialUserMessage = searchParams.get('message')
  const initialModel = searchParams.get('model')
  const initialCategory = searchParams.get('category')
  
  const [messages, setMessages] = useState([])
  const [previewLoading, setPreviewLoading] = useState(false) // Fix: Start with false instead of true
  const [newMessage, setNewMessage] = useState("")
  const [sendingMessage, setSendingMessage] = useState(false)
  const [loadingStage, setLoadingStage] = useState("Initializing...")
  const [lastUserQuery, setLastUserQuery] = useState(initialUserMessage || "")
  const [currentSessionId, setCurrentSessionId] = useState(sessionId)
  const [sandboxUrl, setSandboxUrl] = useState(null)
  const [selectedMessageId, setSelectedMessageId] = useState(null)
  const [conversation, setConversation] = useState(null)

  const [selectedPracticeType, setSelectedPracticeType] = useState("Medical Aesthetics")
  const [selectedModel, setSelectedModel] = useState(initialModel || "gpt-oss-120b")
  const [selectedCategory, setSelectedCategory] = useState(initialCategory || "medical-aesthetics")
  
  const [session, setSession] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)
  const [selectedLogo, setSelectedLogo] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [filePreview, setFilePreview] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [hasProcessedInitialMessage, setHasProcessedInitialMessage] = useState(false)
  
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const documentInputRef = useRef(null)
  const imageInputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const sessionData = await authClient.getSession()
        if (sessionData.data?.user) {
          setSession(sessionData.data)
          setIsAuthenticated(true)
        } else {
          setIsAuthenticated(false)
        }
      } catch (error) {
        setIsAuthenticated(false)
      } finally {
        setAuthChecked(true)
      }
    }
    checkAuth()
  }, [])

  useEffect(() => {
    if (currentSessionId && isAuthenticated && authChecked) {
      loadConversation()
    }
  }, [currentSessionId, isAuthenticated, authChecked])

  useEffect(() => {
    // Fix: Only process initial message if there's an initial message AND no existing messages
    if (initialUserMessage && currentSessionId && isAuthenticated && authChecked && messages.length === 0 && !hasProcessedInitialMessage) {
      setHasProcessedInitialMessage(true)
      handleInitialMessage()
    }
    // Fix: If no initial message but we have a session, just load the conversation
    else if (!initialUserMessage && currentSessionId && isAuthenticated && authChecked && messages.length === 0) {
      // Conversation will be loaded by the first useEffect, just ensure preview loading is false
      setPreviewLoading(false)
    }
  }, [initialUserMessage, currentSessionId, isAuthenticated, authChecked, messages.length, hasProcessedInitialMessage])

  const loadConversation = async () => {
    try {
      const result = await getConversation(currentSessionId)
      
      if (result.success && result.data) {
        setConversation(result.data)
        setMessages(result.data.messages || [])
        
        const assistantMessages = result.data.messages?.filter(m => m.role === 'assistant' && m.sandbox_url)
        if (assistantMessages && assistantMessages.length > 0) {
          const latestMessage = assistantMessages[assistantMessages.length - 1]
          setSandboxUrl(latestMessage.sandbox_url)
          setSelectedMessageId(latestMessage.id)
        }
        // Fix: Always set preview loading to false after loading conversation
        setPreviewLoading(false)
      } else {
        // Fix: Set preview loading to false even if no conversation found
        setPreviewLoading(false)
      }
    } catch (error) {
      console.error('Error loading conversation:', error)
      // Fix: Set preview loading to false on error
      setPreviewLoading(false)
    }
  }

  const handleInitialMessage = async () => {
    if (!initialUserMessage || !currentSessionId) return

    const existingMessage = messages.find(m => 
      m.role === 'user' && m.content === initialUserMessage
    )
    
    if (existingMessage) return

    const userMsg = {
      role: "user",
      content: initialUserMessage,
      created_at: new Date().toISOString()
    }

    // Ensure conversation exists before adding messages
    let conv = conversation
    if (!conv) {
      try {
        const result = await createConversation(
          currentSessionId,
          session.user.id,
          initialUserMessage
        )
        
        if (result.success) {
          conv = result.data
          setConversation(conv)
        } else {
          console.error('Failed to create conversation:', result.error)
          return
        }
      } catch (error) {
        console.error('Error creating conversation:', error)
        return
      }
    }

    // Add user message to conversation
    try {
      const result = await addMessage(currentSessionId, userMsg)
      
      if (result.success) {
        setMessages(prev => [...prev, result.data])
      } else {
        console.error('Failed to add user message:', result.error)
        setMessages(prev => [...prev, userMsg])
      }
    } catch (error) {
      console.error('Error adding user message:', error)
      setMessages(prev => [...prev, userMsg])
    }

    setLastUserQuery(initialUserMessage)
    setPreviewLoading(true) // Fix: Only set to true when actually processing
    setLoadingStage("Processing your request...")

    try {
      const formData = new FormData()
      formData.append('session_id', currentSessionId)
      formData.append('text', initialUserMessage)
      formData.append('llm_model', selectedModel)
      formData.append('schema_type', selectedCategory)
      formData.append('regenerate', 'false')
      if (selectedLogo) {
        formData.append('logo', selectedLogo)
      }

      const response = await fetch('/api/query', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      const backendState = result.state
      let sandboxUrl = null
      let generatedCode = ''
      let conversationId = null

      if (backendState?.context?.final_result?.url) {
        sandboxUrl = backendState.context.final_result.url
      } else if (backendState?.context?.sandbox_result?.url) {
        sandboxUrl = backendState.context.sandbox_result.url
      }

      if (backendState?.context?.generation_result?.e2b_script) {
        generatedCode = backendState.context.generation_result.e2b_script
      }

      if (backendState?.context?.conversation_id) {
        conversationId = backendState.context.conversation_id
      }

      const assistantMsg = {
        role: "assistant",
        content: "Your request has been processed successfully. The app is being generated...",
        created_at: new Date().toISOString()
      }

      // Add assistant message to conversation
      try {
        const addResult = await addMessage(currentSessionId, assistantMsg)
        
        if (addResult.success && addResult.data.id) {
          // Update assistant message with backend data
          const updateResult = await updateAssistantMessage(currentSessionId, addResult.data.id, {
            conversation_id: conversationId,
            sandbox_url: sandboxUrl,
            generated_code: generatedCode,
            metadata: {
              model_used: selectedModel,
              generation_time: Date.now(),
              backend_state: backendState
            }
          })

          if (updateResult.success) {
            const updatedMessage = {
              ...addResult.data,
              conversation_id: conversationId,
              sandbox_url: sandboxUrl,
              generated_code: generatedCode
            }
            setMessages(prev => [...prev, updatedMessage])

            if (sandboxUrl) {
              setSandboxUrl(sandboxUrl)
              setSelectedMessageId(addResult.data.id)
            }
          } else {
            console.error('Failed to update assistant message:', updateResult.error)
            setMessages(prev => [...prev, assistantMsg])
          }
        } else {
          console.error('Failed to add assistant message:', addResult.error)
          setMessages(prev => [...prev, assistantMsg])
        }
      } catch (dbError) {
        console.error('Database error:', dbError)
        setMessages(prev => [...prev, assistantMsg])
      }

      setPreviewLoading(false) // Fix: Set to false after processing

    } catch (error) {
      console.error('API error:', error)
      const errorMsg = {
        role: "assistant",
        content: "Sorry, there was an error processing your request. Please try again.",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
      setPreviewLoading(false) // Fix: Set to false on error
    }
  }

  const handleMessageClick = async (messageId) => {
    const message = messages.find(m => m.id === messageId)
    if (!message || !message.conversation_id) return
    
    // Fix: Set loading state when clicking on a message
    setPreviewLoading(true)
    setLoadingStage("Loading previous version...")
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/sessions/${currentSessionId}/conversations/${message.conversation_id}/restore`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.sandbox_url) {
          setSandboxUrl(data.sandbox_url)
          setSelectedMessageId(messageId)
          // Fix: Set preview loading to false when we get the URL
          setPreviewLoading(false)
        } else {
          // Fix: Set preview loading to false even if no URL
          setPreviewLoading(false)
        }
      } else {
        // Fix: Set preview loading to false on error
        setPreviewLoading(false)
      }
    } catch (error) {
      console.error('Error restoring conversation:', error)
      // Fix: Set preview loading to false on error
      setPreviewLoading(false)
    }
  }

  const handleSendMessage = async (e) => {
    e?.preventDefault()
    if (!newMessage.trim() || sendingMessage || !currentSessionId) return

    const userMsg = {
      role: "user",
      content: newMessage,
      created_at: new Date().toISOString()
    }

    // Ensure conversation exists
    let conv = conversation
    if (!conv) {
      try {
        const result = await createConversation(
          currentSessionId,
          session.user.id,
          newMessage
        )
        
        if (result.success) {
          conv = result.data
          setConversation(conv)
        } else {
          console.error('Failed to create conversation:', result.error)
          return
        }
      } catch (error) {
        console.error('Error creating conversation:', error)
        return
      }
    }

    // Add user message
    try {
      const result = await addMessage(currentSessionId, userMsg)
      
      if (result.success) {
        setMessages(prev => [...prev, result.data])
      } else {
        console.error('Failed to add user message:', result.error)
        setMessages(prev => [...prev, userMsg])
      }
    } catch (error) {
      console.error('Error adding user message:', error)
      setMessages(prev => [...prev, userMsg])
    }

    const messageContent = newMessage
    setLastUserQuery(messageContent)
    setNewMessage("")
    clearAllUploads()
    setSendingMessage(true)
    setPreviewLoading(true) // Fix: Only set to true when actually processing
    setLoadingStage("Processing your request...")

    try {
      const formData = new FormData()
      formData.append('session_id', currentSessionId)
      formData.append('text', messageContent)
      formData.append('llm_model', selectedModel)
      formData.append('schema_type', selectedCategory)
      formData.append('regenerate', 'false')
      
      // Add file uploads
      if (selectedLogo) {
        formData.append('logo', selectedLogo)
      }
      if (selectedFile) {
        formData.append('file', selectedFile)
      }
      if (selectedImage) {
        formData.append('image', selectedImage)
      }

      const response = await fetch('/api/query', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      const backendState = result.state
      let sandboxUrl = null
      let generatedCode = ''
      let conversationId = null

      if (backendState?.context?.final_result?.url) {
        sandboxUrl = backendState.context.final_result.url
      } else if (backendState?.context?.sandbox_result?.url) {
        sandboxUrl = backendState.context.sandbox_result.url
      }

      if (backendState?.context?.generation_result?.e2b_script) {
        generatedCode = backendState.context.generation_result.e2b_script
      }

      if (backendState?.context?.conversation_id) {
        conversationId = backendState.context.conversation_id
      }

      const assistantMsg = {
        role: "assistant",
        content: "Your request has been processed successfully. The app is being updated...",
        created_at: new Date().toISOString()
      }

      // Add assistant message
      try {
        const addResult = await addMessage(currentSessionId, assistantMsg)
        
        if (addResult.success && addResult.data.id) {
          const updateResult = await updateAssistantMessage(currentSessionId, addResult.data.id, {
            conversation_id: conversationId,
            sandbox_url: sandboxUrl,
            generated_code: generatedCode,
            metadata: {
              model_used: selectedModel,
              generation_time: Date.now(),
              backend_state: backendState
            }
          })

          if (updateResult.success) {
            const updatedMessage = {
              ...addResult.data,
              conversation_id: conversationId,
              sandbox_url: sandboxUrl,
              generated_code: generatedCode
            }
            setMessages(prev => [...prev, updatedMessage])

            if (sandboxUrl) {
              setSandboxUrl(sandboxUrl)
              setSelectedMessageId(addResult.data.id)
            }
          } else {
            console.error('Failed to update assistant message:', updateResult.error)
            setMessages(prev => [...prev, assistantMsg])
          }
        } else {
          console.error('Failed to add assistant message:', addResult.error)
          setMessages(prev => [...prev, assistantMsg])
        }
      } catch (dbError) {
        console.error('Database error:', dbError)
        setMessages(prev => [...prev, assistantMsg])
      }

      setPreviewLoading(false) // Fix: Set to false after processing

    } catch (error) {
      console.error('API error:', error)
      const errorMsg = {
        role: "assistant",
        content: "Sorry, there was an error processing your request. Please try again.",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
      setPreviewLoading(false) // Fix: Set to false on error
    } finally {
      setSendingMessage(false)
    }
  }

  const handleRegenerate = async () => {
    if (!lastUserQuery || sendingMessage || !currentSessionId) return

    setSendingMessage(true)
    setPreviewLoading(true) // Fix: Only set to true when actually processing
    setLoadingStage("Regenerating your request...")

    try {
      // Ensure we have a valid session before making the API call
      if (!currentSessionId) {
        throw new Error('No active session found')
      }
      
      const formData = new FormData()
      formData.append('session_id', currentSessionId)
      formData.append('text', '') 
      formData.append('llm_model', selectedModel)
      formData.append('schema_type', selectedCategory)
      formData.append('regenerate', 'true')
      if (selectedLogo) {
        formData.append('logo', selectedLogo)
      }

      const response = await fetch('/api/query', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      const backendState = result.state
      let sandboxUrl = null
      let generatedCode = ''
      let conversationId = null

      if (backendState?.context?.final_result?.url) {
        sandboxUrl = backendState.context.final_result.url
      } else if (backendState?.context?.sandbox_result?.url) {
        sandboxUrl = backendState.context.sandbox_result.url
      }

      if (backendState?.context?.generation_result?.e2b_script) {
        generatedCode = backendState.context.generation_result.e2b_script
      }

      if (backendState?.context?.conversation_id) {
        conversationId = backendState.context.conversation_id
      }

      const assistantMsg = {
        role: "assistant",
        content: "Your request has been regenerated successfully. The app is being updated...",
        created_at: new Date().toISOString()
      }

      try {
        const addResult = await addMessage(currentSessionId, assistantMsg)
        
        if (addResult.success) {
          await updateAssistantMessage(currentSessionId, addResult.data.id, {
            conversation_id: conversationId,
            sandbox_url: sandboxUrl,
            generated_code: generatedCode,
            metadata: {
              model_used: selectedModel,
              generation_time: Date.now(),
              backend_state: backendState
            }
          })

          const updatedMessage = {
            ...addResult.data,
            conversation_id: conversationId,
            sandbox_url: sandboxUrl,
            generated_code: generatedCode
          }
          setMessages(prev => [...prev, updatedMessage])

          if (sandboxUrl) {
            setSandboxUrl(sandboxUrl)
            setSelectedMessageId(addResult.data.id)
          }
        } else {
          setMessages(prev => [...prev, assistantMsg])
        }
      } catch (dbError) {
        setMessages(prev => [...prev, assistantMsg])
      }

      setPreviewLoading(false) // Fix: Set to false after processing

    } catch (error) {
      const errorMsg = {
        role: "assistant",
        content: "Sorry, there was an error regenerating your request. Please try again.",
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMsg])
      setPreviewLoading(false) // Fix: Set to false on error
    } finally {
      setSendingMessage(false)
    }
  }

  const handleLogoSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedLogo(file)
      // Create preview URL
      const previewUrl = URL.createObjectURL(file)
      setLogoPreview(previewUrl)
    }
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
      // Create preview for document
      setFilePreview({
        name: file.name,
        size: file.size,
        type: file.type
      })
    }
  }

  const handleImageSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedImage(file)
      // Create preview URL
      const previewUrl = URL.createObjectURL(file)
      setImagePreview(previewUrl)
    }
  }

  const handleLogoClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileClick = () => {
    documentInputRef.current?.click()
  }

  const handleImageClick = () => {
    imageInputRef.current?.click()
  }

  const clearLogo = () => {
    setSelectedLogo(null)
    if (logoPreview) {
      URL.revokeObjectURL(logoPreview)
      setLogoPreview(null)
    }
  }

  const clearFile = () => {
    setSelectedFile(null)
    setFilePreview(null)
  }

  const clearImage = () => {
    setSelectedImage(null)
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview)
      setImagePreview(null)
    }
  }

  const clearAllUploads = () => {
    clearLogo()
    clearFile()
    clearImage()
  }

  const handleDownload = async () => {
    if (!selectedMessageId || downloading) return
    
    const message = messages.find(m => m.id === selectedMessageId)
    if (!message || !message.conversation_id) {
      alert('No conversation found to download')
      return
    }
    
    setDownloading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/conversations/${message.conversation_id}/download`, {
        method: 'GET'
      })
      
      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`)
      }
      
      // Get filename from response headers or create one
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `project_${message.conversation_id.slice(-8)}.zip`
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download project files. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  if (authChecked && !isAuthenticated) {
    return <SignInForm />
  }

  if (!authChecked) {
    return null
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <div className="bg-background px-4 py-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
                <span className="text-xs font-bold text-primary-foreground">S</span>
              </div>
              <span className="text-sm font-medium text-foreground">spa-sparkle-studio</span>
            </div>
            <Select value={selectedPracticeType} onValueChange={setSelectedPracticeType}>
              <SelectTrigger className="w-[180px] h-6 text-xs rounded-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="text-xs rounded-xl">
                <SelectItem value="Medical Aesthetics">Medical Aesthetics</SelectItem>
                <SelectItem value="Dental">Dental</SelectItem>
                <SelectItem value="Functional Medicine">Functional Medicine</SelectItem>
              </SelectContent>
            </Select>
            {selectedMessageId && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  disabled={downloading}
                  className="flex items-center gap-2 text-xs h-6 px-2"
                  title="Download project files"
                >
                  <Download className="h-3 w-3" />
                  {downloading ? 'Downloading...' : 'Download'}
                </Button>
                <GitHubDeploy 
                  conversationId={messages.find(m => m.id === selectedMessageId)?.conversation_id}
                  disabled={!selectedMessageId}
                />
              </>
            )}
          </div>
          
          {sandboxUrl && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(sandboxUrl, '_blank')}
                className="flex items-center gap-2 text-xs h-6 px-2"
              >
                <ExternalLink className="h-3 w-3" />
                Open in New Tab
              </Button>
              <ModeToggle />
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          <ResizablePanel defaultSize={30} minSize={20}>
            <div className="h-full flex flex-col bg-card">
              <div className="flex-1 min-h-0">
                <ScrollArea className="h-full p-4">
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div
                        key={`${message.role}-${index}-${message.created_at}`}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-lg p-3 ${
                            message.role === 'user'
                              ? 'bg-primary text-primary-foreground ml-4'
                              : `bg-muted text-gray-800 dark:text-gray-200 mr-4 cursor-pointer hover:bg-muted/80 transition-colors ${
                                  selectedMessageId === message.id ? 'ring-2 ring-primary bg-primary/10' : ''
                                }`
                          }`}
                          onClick={() => {
                            if (message.role === 'assistant') {
                              handleMessageClick(message.id)
                            }
                          }}
                        >
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">
                            {message.content}
                          </div>
                          <div className="text-xs opacity-70 mt-2 flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              {message.role === 'assistant' && (
                                <>
                                  <Heart className="h-3 w-3 text-destructive" />
                                  <span>Growth-AI</span>
                                  <span>•</span>
                                  {message.conversation_id ? (
                                    <span className="text-xs bg-primary/20 px-1 rounded">
                                      v{message.conversation_id.slice(-8)}
                                    </span>
                                  ) : (
                                    <span className="text-xs bg-red-500/20 px-1 rounded text-red-500">
                                      no-id
                                    </span>
                                  )}
                                </>
                              )}
                              <span>{new Date(message.created_at).toLocaleTimeString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {sendingMessage && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Heart className="h-4 w-4 text-destructive" />
                        <span className="text-sm">Growth-AI</span>
                        <Lightbulb className="h-4 w-4" />
                        <span className="text-sm">Thinking</span>
                      </div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </div>
                </ScrollArea>
              </div>

              <div className="flex-shrink-0 p-4">
                <form onSubmit={handleSendMessage}>
                  {/* File previews above textarea */}
                  {(logoPreview || filePreview || imagePreview) && (
                    <div className="mb-3 space-y-2">
                      {logoPreview && (
                        <div className="flex items-center gap-2 bg-background/90 backdrop-blur-sm rounded-lg p-2 border border-border">
                          <img 
                            src={logoPreview} 
                            alt="Logo preview" 
                            className="w-8 h-8 object-cover rounded"
                          />
                          <span className="text-xs text-muted-foreground">Logo attached</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-4 w-4 p-0 text-muted-foreground hover:text-foreground ml-auto"
                            onClick={clearLogo}
                          >
                            ×
                          </Button>
                        </div>
                      )}
                      
                      {filePreview && (
                        <div className="flex items-center gap-2 bg-background/90 backdrop-blur-sm rounded-lg p-2 border border-border">
                          <FileText className="w-8 h-8 text-muted-foreground" />
                          <div className="flex-1">
                            <div className="text-xs text-muted-foreground">{filePreview.name}</div>
                            <div className="text-xs text-muted-foreground/70">
                              {(filePreview.size / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-4 w-4 p-0 text-muted-foreground hover:text-foreground"
                            onClick={clearFile}
                          >
                            ×
                          </Button>
                        </div>
                      )}
                      
                      {imagePreview && (
                        <div className="flex items-center gap-2 bg-background/90 backdrop-blur-sm rounded-lg p-2 border border-border">
                          <img 
                            src={imagePreview} 
                            alt="Image preview" 
                            className="w-8 h-8 object-cover rounded"
                          />
                          <span className="text-xs text-muted-foreground">Image attached</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-4 w-4 p-0 text-muted-foreground hover:text-foreground ml-auto"
                            onClick={clearImage}
                          >
                            ×
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="relative">
                    <Textarea
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Ask Growth-AI..."
                      className="min-h-[100px] resize-none bg-background border-border text-foreground placeholder-muted-foreground pr-12 rounded-xl focus:ring-2 focus:ring-ring focus:border-transparent"
                      disabled={sendingMessage}
                    />
                    
                    <div className="absolute bottom-2 flex items-center justify-between w-full">
                      {/* Upload buttons on the left */}
                      <div className="flex items-center gap-2 ml-2">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          onChange={handleLogoSelect}
                          className="hidden"
                        />
                        <input
                          ref={documentInputRef}
                          type="file"
                          accept=".pdf,.doc,.docx,.txt,.md"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                        <input
                          ref={imageInputRef}
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          className="hidden"
                        />
                        
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon" 
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground cursor-pointer rounded-full border border-border/50"
                          onClick={handleFileClick}
                          disabled={sendingMessage}
                          title="Add document"
                        >
                          <Plus className="h-3 w-3" />
                        </Button>
                        
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="icon" 
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground cursor-pointer rounded-full border border-border/50"
                          onClick={handleImageClick}
                          disabled={sendingMessage}
                          title="Add image"
                        >
                          <ImagePlus className="h-3 w-3" />
                        </Button>
                      </div>
                      
                      {/* Action buttons on the right */}
                      <div className="flex items-center gap-2 mr-2">
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="sm" 
                          className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground cursor-pointer rounded-full border border-border/50"
                          onClick={handleLogoClick}
                          disabled={sendingMessage}
                          title="Add logo"
                        >
                          Add Logo
                        </Button>
                        <Button 
                          type="button" 
                          variant="ghost" 
                          size="icon" 
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground cursor-pointer rounded-full"
                          onClick={handleRegenerate}
                          disabled={!lastUserQuery || sendingMessage}
                          title="Regenerate"
                        >
                          <RefreshCw className={`h-4 w-4 ${sendingMessage ? 'animate-spin' : ''}`} />
                        </Button>
                        
                        <Button 
                          type="submit" 
                          size="icon"
                          className="h-6 w-6 p-0 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full cursor-pointer"
                          disabled={sendingMessage || (!newMessage.trim() && !selectedLogo && !selectedFile && !selectedImage)}
                        >
                          {sendingMessage ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <ArrowUp className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="md:hidden" />

          <ResizablePanel defaultSize={70} minSize={40}>
            <div className="h-full flex flex-col bg-background">
              <div className="flex-1 p-1">
                {previewLoading ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-6">
                      <div className="relative">
                        <Heart className="h-16 w-16 mx-auto text-muted-foreground animate-pulse" />
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Loader2 className="h-8 w-8 text-primary animate-spin" />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <h2 className="text-xl font-semibold text-foreground">
                          Building your app...
                        </h2>
                        <p className="text-sm text-muted-foreground">{loadingStage}</p>
                      </div>
                      
                      <div className="space-y-3 text-left max-w-sm">
                        <div className="flex items-center gap-3 text-sm">
                          <div className="w-4 h-4 border border-border rounded flex items-center justify-center">
                            <Brain className="h-2 w-2 text-primary animate-pulse" />
                          </div>
                          <span>Processing your request...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : sandboxUrl ? (
                  <div className="h-full relative">
                    <iframe
                      key={`${selectedMessageId}-${sandboxUrl}`}
                      src={sandboxUrl}
                      className="w-full h-full rounded-lg border border-border shadow-sm"
                      title="App Preview"
                    />
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-muted-foreground">
                    <div className="text-center space-y-4">
                      <Code2 className="h-16 w-16 mx-auto text-muted-foreground" />
                      <div className="space-y-2">
                        <h3 className="text-lg font-semibold text-foreground">
                          App Preview
                        </h3>
                        <p className="text-sm text-muted-foreground max-w-md">
                          Your generated app will appear here once the backend processing is complete.
                        </p>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        The preview will show your live application
                      </div>
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