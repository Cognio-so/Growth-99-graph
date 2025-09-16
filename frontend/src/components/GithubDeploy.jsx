"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Github, Loader2, ExternalLink, Check, AlertCircle, Zap, User } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { authClient } from "@/lib/auth-client"

export default function GitHubDeploy({ conversationId, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isDeploying, setIsDeploying] = useState(false)
  const [deploymentStep, setDeploymentStep] = useState("")
  
  // User session state
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  
  // Form states
  const [repoName, setRepoName] = useState("")
  const [description, setDescription] = useState("")
  const [isPrivate, setIsPrivate] = useState(false)
  
  // Results
  const [deploymentResult, setDeploymentResult] = useState(null)
  const [error, setError] = useState(null)

  // Check user session
  useEffect(() => {
    const checkSession = async () => {
      try {
        const session = await authClient.getSession()
        setUser(session.data?.user || null)
      } catch (error) {
        console.error('Error checking session:', error)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    checkSession()
  }, [])

  // Listen for auth result from popup
  useEffect(() => {
    const handleMessage = (event) => {
      if (event.origin !== window.location.origin) return
      
      if (event.data.type === 'GITHUB_AUTH_RESULT') {
        const { success, accessToken, error } = event.data
        
        if (success && accessToken) {
          proceedWithDeployment(accessToken)
        } else {
          setError(error || 'GitHub authentication failed')
          setIsDeploying(false)
          setDeploymentStep("")
        }
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  // Handle GitHub authentication and deployment
  const handleGitHubDeploy = async () => {
    if (!repoName.trim()) {
      setError("Repository name is required")
      return
    }

    if (!user) {
      setError("Please sign in first")
      return
    }

    setIsDeploying(true)
    setError(null)
    setDeploymentResult(null)

    try {
      // Step 1: Download the project files from backend
      setDeploymentStep("Downloading project files...")
      
      const downloadResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/conversations/${conversationId}/download`, {
        method: 'GET'
      })
      
      if (!downloadResponse.ok) {
        throw new Error(`Failed to download files: ${downloadResponse.status}`)
      }
      
      const projectBlob = await downloadResponse.blob()
      
      // Step 2: Get GitHub client ID
      setDeploymentStep("Getting GitHub configuration...")
      
      const clientIdResponse = await fetch('/api/auth/github/client-id')
      if (!clientIdResponse.ok) {
        throw new Error('Failed to get GitHub configuration')
      }
      
      const clientIdData = await clientIdResponse.json()
      if (!clientIdData.clientId) {
        throw new Error('GitHub client ID not configured')
      }
      
      // Step 3: Open GitHub OAuth in new tab
      setDeploymentStep("Opening GitHub authentication...")
      
      const redirectUri = `${window.location.origin}/api/auth/callback/github`
      const scope = 'repo'
      const state = `deploy-${conversationId}-${Date.now()}`
      
      // Store deployment data in sessionStorage for after OAuth
      sessionStorage.setItem('pendingDeployment', JSON.stringify({
        conversationId,
        repoName: repoName.trim(),
        description: description.trim() || `Generated React app from Growth-99-graph`,
        isPrivate,
        projectBlob: await blobToBase64(projectBlob)
      }))
      
      // Open GitHub OAuth in new tab with specific window features
      const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientIdData.clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${scope}&state=${state}`
      
      // Try to open popup first
      let authWindow = window.open(
        githubAuthUrl, 
        'github-auth', 
        'width=600,height=700,scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no'
      )
      
      // Check if popup was blocked
      if (!authWindow || authWindow.closed || typeof authWindow.closed === 'undefined') {
        // Popup was blocked, show instructions to user
        setError('Popup blocked! Please click the "Open GitHub Auth" button below to continue.')
        setDeploymentStep("Waiting for GitHub authentication...")
        
        // Show a button to manually open the auth URL
        const manualAuthButton = document.createElement('div')
        manualAuthButton.innerHTML = `
          <div style="margin-top: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background: #f9f9f9;">
            <p style="margin: 0 0 10px 0; font-size: 14px;">Your browser blocked the popup. Please click the button below to open GitHub authentication:</p>
            <button onclick="window.open('${githubAuthUrl}', '_blank')" style="padding: 8px 16px; background: #24292e; color: white; border: none; border-radius: 4px; cursor: pointer;">
              Open GitHub Auth
            </button>
          </div>
        `
        
        // Add the button to the dialog (you might want to handle this differently)
        const dialogContent = document.querySelector('[role="dialog"]')
        if (dialogContent) {
          dialogContent.appendChild(manualAuthButton)
        }
        
        // Listen for the auth result
        const checkAuthResult = setInterval(() => {
          const authResult = sessionStorage.getItem('githubAuthResult')
          if (authResult) {
            clearInterval(checkAuthResult)
            try {
              const { success, accessToken } = JSON.parse(authResult)
              if (success && accessToken) {
                proceedWithDeployment(accessToken)
              } else {
                setError('GitHub authentication failed')
                setIsDeploying(false)
                setDeploymentStep("")
              }
            } catch (parseError) {
              console.error('Error parsing auth result:', parseError)
              setError('Authentication result parsing failed')
              setIsDeploying(false)
              setDeploymentStep("")
            }
            sessionStorage.removeItem('githubAuthResult')
            // Remove the manual button
            if (manualAuthButton.parentNode) {
              manualAuthButton.parentNode.removeChild(manualAuthButton)
            }
          }
        }, 1000)
        
        return
      }
      
      // Focus the new window
      authWindow.focus()
      
      // Listen for the auth window to close or receive message
      const checkClosed = setInterval(() => {
        try {
          if (authWindow.closed) {
            clearInterval(checkClosed)
            // Check if we have the auth result
            const authResult = sessionStorage.getItem('githubAuthResult')
            if (authResult) {
              try {
                const { success, accessToken } = JSON.parse(authResult)
                if (success && accessToken) {
                  proceedWithDeployment(accessToken)
                } else {
                  setError('GitHub authentication failed')
                  setIsDeploying(false)
                  setDeploymentStep("")
                }
              } catch (parseError) {
                console.error('Error parsing auth result:', parseError)
                setError('Authentication result parsing failed')
                setIsDeploying(false)
                setDeploymentStep("")
              }
              sessionStorage.removeItem('githubAuthResult')
            } else {
              setError('GitHub authentication was cancelled')
              setIsDeploying(false)
              setDeploymentStep("")
            }
          }
        } catch (error) {
          // Handle cross-origin errors
          clearInterval(checkClosed)
          setError('Authentication window was closed')
          setIsDeploying(false)
          setDeploymentStep("")
        }
      }, 1000)
      
    } catch (error) {
      console.error('Deployment error:', error)
      setError(error.message)
      setIsDeploying(false)
      setDeploymentStep("")
    }
  }

  // Proceed with deployment after successful authentication
  const proceedWithDeployment = async (accessToken) => {
    try {
      setDeploymentStep("Creating GitHub repository...")
      
      const pendingDeployment = JSON.parse(sessionStorage.getItem('pendingDeployment') || '{}')
      
      // Create FormData to send the zip file and metadata
      const formData = new FormData()
      formData.append('projectFiles', base64ToBlob(pendingDeployment.projectBlob))
      formData.append('repoName', pendingDeployment.repoName)
      formData.append('description', pendingDeployment.description)
      formData.append('isPrivate', pendingDeployment.isPrivate.toString())
      formData.append('accessToken', accessToken)
      
      const deployResponse = await fetch('/api/deploy/github', {
        method: 'POST',
        body: formData
      })
      
      if (!deployResponse.ok) {
        const errorData = await deployResponse.json()
        throw new Error(errorData.error || 'Failed to create GitHub repository')
      }
      
      const deployData = await deployResponse.json()
      
      setDeploymentStep("Repository created successfully!")
      
      // Step 3: Generate Vercel deployment URL
      const vercelUrl = `https://vercel.com/new/clone?repository-url=${deployData.repoUrl}`
      
      setDeploymentResult({
        repoUrl: deployData.repoUrl,
        vercelUrl: vercelUrl,
        repoName: pendingDeployment.repoName,
        filesUploaded: deployData.filesUploaded
      })
      
      // Clean up session storage
      sessionStorage.removeItem('pendingDeployment')
      
    } catch (error) {
      console.error('Deployment error:', error)
      setError(error.message)
    } finally {
      setIsDeploying(false)
      setDeploymentStep("")
    }
  }

  // Helper functions
  const blobToBase64 = (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  const base64ToBlob = (base64) => {
    const arr = base64.split(',')
    const mime = arr[0].match(/:(.*?);/)[1]
    const bstr = atob(arr[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n)
    }
    return new Blob([u8arr], { type: mime })
  }

  const resetForm = () => {
    setRepoName("")
    setDescription("")
    setIsPrivate(false)
    setDeploymentResult(null)
    setError(null)
  }

  const handleOpenChange = (open) => {
    setIsOpen(open)
    if (!open && !isDeploying) {
      resetForm()
    }
  }

  if (isLoading) {
    return (
      <Button
        variant="outline"
        size="sm"
        disabled
        className="flex items-center gap-2 text-xs h-6 px-2"
      >
        <Loader2 className="h-3 w-3 animate-spin" />
        Loading...
      </Button>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          className="flex items-center gap-2 text-xs h-6 px-2"
          title="Deploy to GitHub & Vercel"
          onClick={() => {
            console.log('Deploy button clicked!')
            setIsOpen(true)
          }}
        >
          <Github className="h-3 w-3" />
          Deploy
        </Button>
      </DialogTrigger>
      
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            Deploy to GitHub & Vercel
          </DialogTitle>
          <DialogDescription>
            Create a GitHub repository with your generated code and deploy it to Vercel.
          </DialogDescription>
        </DialogHeader>

        {/* GitHub Authentication Section */}
        {!user ? (
          <div className="grid gap-4 py-4">
            <Alert>
              <Github className="h-4 w-4" />
              <AlertDescription>
                <strong>Sign in required</strong>
                <br />
                <span className="text-sm text-muted-foreground">
                  Please sign in to deploy your app to GitHub and Vercel.
                </span>
              </AlertDescription>
            </Alert>
            
            <Button
              onClick={() => authClient.signIn.social({ provider: "github" })}
              className="w-full flex items-center gap-2"
            >
              <Github className="h-4 w-4" />
              Sign in with GitHub
            </Button>
          </div>
        ) : (
          <>
            {/* GitHub User Info */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg mb-4">
              <div className="flex items-center gap-3">
                <img 
                  src={user.image} 
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
                <div>
                  <p className="font-medium">{user.name}</p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => authClient.signOut()}
                className="flex items-center gap-2"
              >
                <User className="h-4 w-4" />
                Sign Out
              </Button>
            </div>

            {!deploymentResult && (
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="repoName">Repository Name *</Label>
                  <Input
                    id="repoName"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                    placeholder="my-awesome-app"
                    disabled={isDeploying}
                  />
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Generated React app from Growth-99-graph"
                    disabled={isDeploying}
                    rows={2}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="isPrivate"
                    checked={isPrivate}
                    onChange={(e) => setIsPrivate(e.target.checked)}
                    disabled={isDeploying}
                    className="rounded"
                  />
                  <Label htmlFor="isPrivate" className="text-sm">
                    Make repository private
                  </Label>
                </div>
              </div>
            )}

            {deploymentResult && (
              <div className="grid gap-4 py-4">
                <Alert>
                  <Check className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Repository created successfully!</strong>
                    <br />
                    <span className="text-sm text-muted-foreground">
                      Uploaded {deploymentResult.filesUploaded} files
                    </span>
                  </AlertDescription>
                </Alert>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">GitHub Repository</p>
                      <p className="text-sm text-muted-foreground">{deploymentResult.repoName}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(deploymentResult.repoUrl, '_blank')}
                      className="flex items-center gap-2"
                    >
                      <Github className="h-4 w-4" />
                      View Repo
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">Deploy to Vercel</p>
                      <p className="text-sm text-muted-foreground">One-click deployment</p>
                    </div>
                    <Button
                      onClick={() => window.open(deploymentResult.vercelUrl, '_blank')}
                      className="flex items-center gap-2"
                    >
                      <Zap className="h-4 w-4" />
                      Deploy Now
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {isDeploying && (
              <div className="flex items-center gap-2 py-4">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">{deploymentStep}</span>
              </div>
            )}

            <DialogFooter>
              {!deploymentResult && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setIsOpen(false)}
                    disabled={isDeploying}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleGitHubDeploy}
                    disabled={isDeploying || !repoName.trim()}
                  >
                    {isDeploying ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Deploying...
                      </>
                    ) : (
                      <>
                        <Github className="h-4 w-4 mr-2" />
                        Deploy to GitHub
                      </>
                    )}
                  </Button>
                </>
              )}
              
              {deploymentResult && (
                <Button onClick={() => setIsOpen(false)}>
                  Close
                </Button>
              )}
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}