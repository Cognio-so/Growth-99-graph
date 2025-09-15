
import MainInput from '@/components/MainInput'
import { Navbar } from '@/components/ui/Navbar'

export default function Home() {
  return (
    <div className="h-screen bg-background overflow-hidden flex flex-col">
      {/* Navbar Wrapper */}
      <div className="flex-shrink-0">
        <Navbar />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <MainInput />
      </div>
    </div>
  )
}
