"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { Search, ExternalLink, Calendar, Eye, Star, MoreHorizontal, Code2, Loader2, Trash2, Image as ImageIcon, Globe, Smartphone, Wrench, Building2, Palette, Zap, Database, ShoppingCart, Users, BarChart3 } from "lucide-react"
import { authClient } from "@/lib/auth-client"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function ProjectHistory() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [authLoading, setAuthLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortBy, setSortBy] = useState("newest")
  const [filterBy, setFilterBy] = useState("all")
  const [session, setSession] = useState(null)
  const [deletingProjectId, setDeletingProjectId] = useState(null)
  const router = useRouter()

  useEffect(() => {
    const getSession = async () => {
      try {
        setAuthLoading(true)
        const sessionData = await authClient.getSession()
        setSession(sessionData.data)
      } catch (error) {
        console.error("Error getting session:", error)
        setSession(null)
      } finally {
        setAuthLoading(false)
      }
    }
    getSession()
  }, [])

  useEffect(() => {
    if (!authLoading && session?.user) {
      loadProjects()
    } else if (!authLoading && !session?.user) {
      setLoading(false)
    }
  }, [session, authLoading])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/conversations')
      
      if (!response.ok) {
        throw new Error('Failed to fetch conversations')
      }
      
      const data = await response.json()
      setProjects(data.projects || [])
    } catch (error) {
      console.error("Error loading projects:", error)
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteProject = async (projectId) => {
    try {
      setDeletingProjectId(projectId)
      const response = await fetch(`/api/conversations?sessionId=${projectId}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error('Failed to delete project')
      }
      
      // Remove the project from the local state
      setProjects(prevProjects => prevProjects.filter(project => project.id !== projectId))
    } catch (error) {
      console.error("Error deleting project:", error)
      alert('Failed to delete project. Please try again.')
    } finally {
      setDeletingProjectId(null)
    }
  }

  // Generate different types of images based on project type and name
  const getProjectImage = (project) => {
    const projectType = project.type?.toLowerCase() || 'website'
    const projectName = project.name || 'Project'
    const firstLetter = projectName.charAt(0).toUpperCase()
    
    // Color schemes for different project types
    const colorSchemes = {
      website: {
        gradient: 'from-blue-500/20 to-purple-600/20',
        icon: Globe,
        bgColor: 'bg-blue-500/10',
        iconColor: 'text-blue-600'
      },
      app: {
        gradient: 'from-green-500/20 to-emerald-600/20',
        icon: Smartphone,
        bgColor: 'bg-green-500/10',
        iconColor: 'text-green-600'
      },
      tools: {
        gradient: 'from-orange-500/20 to-red-600/20',
        icon: Wrench,
        bgColor: 'bg-orange-500/10',
        iconColor: 'text-orange-600'
      },
      b2b: {
        gradient: 'from-indigo-500/20 to-blue-600/20',
        icon: Building2,
        bgColor: 'bg-indigo-500/10',
        iconColor: 'text-indigo-600'
      },
      ecommerce: {
        gradient: 'from-pink-500/20 to-rose-600/20',
        icon: ShoppingCart,
        bgColor: 'bg-pink-500/10',
        iconColor: 'text-pink-600'
      },
      dashboard: {
        gradient: 'from-cyan-500/20 to-teal-600/20',
        icon: BarChart3,
        bgColor: 'bg-cyan-500/10',
        iconColor: 'text-cyan-600'
      },
      portfolio: {
        gradient: 'from-purple-500/20 to-violet-600/20',
        icon: Palette,
        bgColor: 'bg-purple-500/10',
        iconColor: 'text-purple-600'
      },
      default: {
        gradient: 'from-gray-500/20 to-slate-600/20',
        icon: Code2,
        bgColor: 'bg-gray-500/10',
        iconColor: 'text-gray-600'
      }
    }

    const scheme = colorSchemes[projectType] || colorSchemes.default
    const IconComponent = scheme.icon

    return {
      scheme,
      IconComponent,
      firstLetter
    }
  }

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         project.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filterBy === "all" || project.type.toLowerCase().includes(filterBy.toLowerCase())
    return matchesSearch && matchesFilter
  })

  const sortedProjects = [...filteredProjects].sort((a, b) => {
    if (sortBy === "newest") {
      return new Date(b.lastEdited) - new Date(a.lastEdited)
    } else if (sortBy === "oldest") {
      return new Date(a.lastEdited) - new Date(b.lastEdited)
    } else if (sortBy === "name") {
      return a.name.localeCompare(b.name)
    }
    return 0
  })

  const handleProjectClick = (project) => {
    // Navigate to ResultView with the session ID
    router.push(`/result?session=${project.sessionId}`)
  }

  // Show loading spinner while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // Show sign-in prompt only after auth check is complete and user is not authenticated
  if (!session?.user) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Please sign in to view your projects</h2>
          <Button asChild>
            <Link href="/sign-in">Sign In</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">My Growth-AI Workspace</h1>
          <Button variant="outline" size="sm">
            View all
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Newest first</SelectItem>
                <SelectItem value="oldest">Oldest first</SelectItem>
                <SelectItem value="name">Name A-Z</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterBy} onValueChange={setFilterBy}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All creations</SelectItem>
                <SelectItem value="website">Website</SelectItem>
                <SelectItem value="app">Consumer App</SelectItem>
                <SelectItem value="tools">Internal Tools</SelectItem>
                <SelectItem value="b2b">B2B App</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <div className="aspect-video bg-muted rounded-t-lg" />
                <CardContent className="p-4">
                  <div className="h-4 bg-muted rounded mb-2" />
                  <div className="h-3 bg-muted rounded w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {sortedProjects.map((project) => {
              const { scheme, IconComponent, firstLetter } = getProjectImage(project)
              
              return (
                <Card 
                  key={project.id} 
                  className="group hover:shadow-lg transition-all duration-200 cursor-pointer overflow-hidden"
                  onClick={() => handleProjectClick(project)}
                >
                  <div className={`aspect-video bg-gradient-to-br ${scheme.gradient} relative overflow-hidden`}>
                    {/* Main background pattern */}
                    <div className="absolute inset-0">
                      <div className={`absolute inset-0 ${scheme.bgColor}`} />
                      
                      {/* Geometric pattern overlay */}
                      <div className="absolute inset-0 opacity-20">
                        <div className="absolute top-4 left-4 w-8 h-8 border-2 border-current rounded-full" />
                        <div className="absolute top-8 right-8 w-4 h-4 bg-current rounded-full" />
                        <div className="absolute bottom-6 left-8 w-6 h-6 border-2 border-current rotate-45" />
                        <div className="absolute bottom-4 right-4 w-3 h-3 bg-current rounded-full" />
                      </div>
                    </div>

                    {/* Central icon and letter */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className={`w-16 h-16 ${scheme.bgColor} rounded-full flex items-center justify-center mb-2 mx-auto`}>
                          <IconComponent className={`h-8 w-8 ${scheme.iconColor}`} />
                        </div>
                        <div className={`text-2xl font-bold ${scheme.iconColor} opacity-80`}>
                          {firstLetter}
                        </div>
                      </div>
                    </div>

                    {/* Animated elements */}
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <div className="absolute top-2 left-2 w-2 h-2 bg-current rounded-full animate-pulse" />
                      <div className="absolute top-4 right-4 w-1 h-1 bg-current rounded-full animate-pulse delay-100" />
                      <div className="absolute bottom-4 left-4 w-1.5 h-1.5 bg-current rounded-full animate-pulse delay-200" />
                    </div>
                    
                    {/* Badge */}
                    <div className="absolute top-2 right-2">
                      <Badge variant="secondary" className="text-xs bg-background/90 backdrop-blur-sm">
                        {project.type}
                      </Badge>
                    </div>
                    
                    {/* Live preview indicator */}
                    {project.sandboxUrl && (
                      <div className="absolute top-2 left-2">
                        <Badge variant="outline" className="text-xs bg-background/90 backdrop-blur-sm">
                          <Zap className="h-3 w-3 mr-1" />
                          Live
                        </Badge>
                      </div>
                    )}
                    
                    {/* Open button */}
                    <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button 
                        size="sm" 
                        variant="secondary" 
                        className="h-8 w-8 p-0 bg-background/90 backdrop-blur-sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleProjectClick(project)
                        }}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-sm truncate flex-1">{project.name}</h3>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="h-6 w-6 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                              onClick={(e) => e.stopPropagation()}
                              disabled={deletingProjectId === project.id}
                            >
                              {deletingProjectId === project.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Project</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete "{project.name}"? This action cannot be undone and will permanently remove the project and all its data.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDeleteProject(project.id)
                                }}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{project.description}</p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{project.lastEdited}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Code2 className="h-3 w-3" />
                        <span>{project.messageCount} messages</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}

        {/* Show More Button */}
        {sortedProjects.length > 0 && (
          <div className="text-center mt-8">
            <Button variant="outline" size="lg">
              Show more
            </Button>
          </div>
        )}

        {/* Empty State */}
        {!loading && sortedProjects.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Eye className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No projects found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? "Try adjusting your search terms" : "Start building your first project"}
            </p>
            <Button asChild>
              <Link href="/">Create Project</Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
