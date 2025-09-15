import { NextResponse } from 'next/server'
import { auth } from '@clerk/nextjs/server'
import { prisma } from '@/lib/db'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL

export async function POST(request) {
  try {
    const { userId } = await auth()
    
    const formData = await request.formData()
    
    // If user is authenticated, create or get session
    let sessionId = formData.get('session_id')
    if (userId && sessionId) {
      try {
        // Create or update session in database
        await prisma.session.upsert({
          where: { id: sessionId },
          update: {
            userId: userId,
            updatedAt: new Date(),
          },
          create: {
            id: sessionId,
            userId: userId,
            title: formData.get('text')?.substring(0, 100) || 'New Session',
          },
        })
      } catch (error) {
        console.error('Error saving session:', error)
        // Continue with the request even if session save fails
      }
    }
    
    // Forward the request to your backend
    const backendResponse = await fetch(`${BACKEND_URL}/api/query`, {
      method: 'POST',
      body: formData,
    })
    
    const data = await backendResponse.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    )
  }
}
