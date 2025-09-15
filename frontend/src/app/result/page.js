import { Suspense } from 'react'
import ResultView from '@/components/ResultView'

function ResultPageContent() {
  return <ResultView />
}

export default function ResultPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResultPageContent />
    </Suspense>
  )
}
