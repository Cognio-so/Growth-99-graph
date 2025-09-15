"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Plus, ArrowUp, Loader2 } from "lucide-react"

export default function MainInput() {
  const [input, setInput] = useState("")
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState("k2") 
  const router = useRouter()

  const availableModels = [
    { value: "k2", label: "K2 (Kimi)" },
    { value: "claude", label: "Claude 3.5 Sonnet" },
    { value: "claude-haiku", label: "Claude 3.5 Haiku" },
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "glm-4.5", label: "GLM-4.5" },
    { value: "groq-default", label: "Groq Default" }
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    setLoading(true)
    
    try {
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      const encodedInput = encodeURIComponent(input)
      const encodedModel = encodeURIComponent(selectedModel)
      router.push(`/result?session=${sessionId}&message=${encodedInput}&model=${encodedModel}`)
      
      
    } catch (error) {
      console.error('Error submitting query:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* Main Content - perfectly centered */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6">
        <div className="text-center mb-12">
          <h1 className="text-6xl md:text-7xl font-bold text-foreground mb-4">
            Build something{" "}
            <span className="text-primary">Growth-AI</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Create apps and websites by chatting with AI
          </p>
        </div>

        {/* Input Box */}
        <div className="w-full max-w-4xl">
          <form onSubmit={handleSubmit} className="relative">
            <div className="relative bg-card/50 backdrop-blur-sm rounded-4xl border border-border p-3 shadow-2xl shadow-primary/20 hover:shadow-[0_0_30px_rgba(217,119,87,0.4)] hover:border-[#d97757] transition-all duration-300">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Growth-AI to create a landing page for my..."
                className="w-full bg-transparent text-white placeholder-muted-foreground text-lg resize-none outline-none min-h-[40px] max-h-[200px]"
                disabled={loading}
                rows={2}
              />
              
              {/* Bottom controls */}
              <div className="flex items-center justify-between mt-4">
                <div className="flex items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => document.getElementById('file-input').click()}
                    className="w-8 h-8 rounded-full cursor-pointer"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                  <input
                    id="file-input"
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.docx,.txt,.json,.md"
                    className="hidden"
                    disabled={loading}
                  />
                </div>
                
                <div className="flex items-center gap-3">
                  {/* Model Selector */}
                  <Select value={selectedModel} onValueChange={setSelectedModel} disabled={loading}>
                    <SelectTrigger className="w-[140px] h-8 text-xs rounded-full cursor-pointer">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels.map((model) => (
                        <SelectItem key={model.value} value={model.value}>
                          {model.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Button
                    type="submit"
                    size="icon"
                    disabled={loading || !input.trim()}
                    className="w-8 h-8 rounded-full cursor-pointer"
                  >
                    {loading ? (
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
      </main>
    </div>
  )
}
