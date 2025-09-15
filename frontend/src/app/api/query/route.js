import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL

export async function POST(request) {
  try {

    const formData = await request.formData()


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
