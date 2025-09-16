"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, Sparkles, LogOut, User } from "lucide-react"
import { authClient } from "@/lib/auth-client"

import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ModeToggle } from "@/components/ui/theme-toggle"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Home", href: "/" },
  { name: "Projects", href: "/projects" },
  { name: "Templates", href: "/templates" },
]

export function Navbar() {
  const [isOpen, setIsOpen] = React.useState(false)
  const [session, setSession] = React.useState(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const pathname = usePathname()

  // Get session on component mount
  React.useEffect(() => {
    const getSession = async () => {
      try {
        const sessionData = await authClient.getSession()
        setSession(sessionData.data)
      } catch (error) {
        console.error("Error getting session:", error)
        setSession(null)
      } finally {
        setIsLoading(false)
      }
    }

    getSession()
  }, [])

  const handleSignOut = async () => {
    try {
      await authClient.signOut()
      setSession(null)
      window.location.href = "/"
    } catch (error) {
      console.error("Sign out error:", error)
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full bg-background/95 backdrop-blur">
      <div className="container mx-auto px-4">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Growth-AI
            </span>
          </Link>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            <ModeToggle />
            
            {isLoading ? (
              <div className="w-8 h-8 rounded-full bg-muted animate-pulse" />
            ) : session?.user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={session.user.image} alt={session.user.name} />
                      <AvatarFallback>
                        {session.user.name?.charAt(0)?.toUpperCase() || "U"}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <div className="flex items-center justify-start gap-2 p-2">
                    <div className="flex flex-col space-y-1 leading-none">
                      {session.user.name && (
                        <p className="font-medium">{session.user.name}</p>
                      )}
                      {session.user.email && (
                        <p className="w-[200px] truncate text-sm text-muted-foreground">
                          {session.user.email}
                        </p>
                      )}
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link href="/profile" className="cursor-pointer">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Sign out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/sign-in">Sign In</Link>
                </Button>
                <Button size="sm" asChild>
                  <Link href="/sign-up">Sign Up</Link>
                </Button>
              </div>
            )}

            {/* Mobile menu */}
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden">
                  <Menu className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right">
                <SheetHeader>
                  <SheetTitle>Growth-AI</SheetTitle>
                </SheetHeader>
                
                <div className="mt-6 flex flex-col space-y-4">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setIsOpen(false)}
                      className={cn(
                        "text-sm font-medium transition-colors hover:text-primary",
                        pathname === item.href ? "text-primary" : "text-muted-foreground"
                      )}
                    >
                      {item.name}
                    </Link>
                  ))}
                  
                  {session?.user ? (
                    <div className="pt-4 border-t">
                      <div className="flex items-center space-x-2 mb-4">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={session.user.image} alt={session.user.name} />
                          <AvatarFallback>
                            {session.user.name?.charAt(0)?.toUpperCase() || "U"}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">{session.user.name}</p>
                          <p className="text-xs text-muted-foreground">{session.user.email}</p>
                        </div>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleSignOut}
                        className="w-full"
                      >
                        <LogOut className="mr-2 h-4 w-4" />
                        Sign out
                      </Button>
                    </div>
                  ) : (
                    <div className="pt-4 border-t space-y-2">
                      <Button variant="outline" size="sm" asChild className="w-full">
                        <Link href="/sign-in" onClick={() => setIsOpen(false)}>
                          Sign In
                        </Link>
                      </Button>
                      <Button size="sm" asChild className="w-full">
                        <Link href="/sign-up" onClick={() => setIsOpen(false)}>
                          Sign Up
                        </Link>
                      </Button>
                    </div>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </header>
  )
}