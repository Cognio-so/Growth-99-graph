"use client"
import MainInput from '@/components/MainInput'
import ProjectHistory from '@/components/ProjectHistory'
import { Navbar } from '@/components/ui/Navbar'

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navbar */}
      <div className="flex-shrink-0">
        <Navbar />
      </div>
      
      {/* Main Content Container */}
      <div className="container mx-auto px-4 py-8">
        {/* Main Input Section */}
        <div className="mb-12">
          <MainInput />
        </div>
        
        {/* Project History Section */}
        <div className="bg-card/50 backdrop-blur-sm rounded-3xl border border-border p-6 shadow-2xl hover:shadow-[0_0_30px_rgba(217,119,87,0.4)] hover:border-[#d97757] transition-all duration-300">
          <ProjectHistory />
        </div>
      </div>
    </div>
  )
}
