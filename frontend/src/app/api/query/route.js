import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { incrementUserQueries } from '@/lib/actions/user-actions'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL

export async function POST(request) {
  try {
    // Get authenticated user
    const { userId } = await auth()
    
    const formData = await request.formData()

    // Forward the request to your backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/query`, {
      method: 'POST',
      body: formData,
    })

    const data = await backendResponse.json()
    
    // Increment user query count if user is authenticated
    if (userId) {
      try {
        await incrementUserQueries(userId)
      } catch (error) {
        console.error('Error incrementing user queries:', error)
        // Don't fail the request if query tracking fails
      }
    }
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    )
  }
}
