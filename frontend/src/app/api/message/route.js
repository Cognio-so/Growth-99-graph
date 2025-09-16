import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL

export async function POST(request) {
  try {
    const body = await request.json()
    const { session_id, message } = body

    // Forward the request to backend to save message
    const backendResponse = await fetch(`${BACKEND_URL}/api/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id,
        message
      }),
    })

    const data = await backendResponse.json()
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('Message API Error:', error)
    return NextResponse.json(
      { error: 'Failed to save message' },
      { status: 500 }
    )
  }
}
