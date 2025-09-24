import { NextResponse } from 'next/server'
import { getUserConversations, deleteConversation } from '@/lib/actions/conversation-actions'
import { getServerSession } from '@/lib/get-session'

export async function GET(request) {
  try {
    const session = await getServerSession()
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const result = await getUserConversations(session.user.id, 20)
    
    if (!result.success) {
      return NextResponse.json({ error: 'Failed to fetch conversations' }, { status: 500 })
    }

    const conversations = result.data
    
    // Transform conversations to project format
    const projects = conversations.map(conv => {
      const lastMessage = conv.messages?.[conv.messages.length - 1]
      const sandboxUrl = lastMessage?.sandbox_url
      
      return {
        id: conv.session_id,
        name: conv.title || `Project ${conv.session_id.slice(-8)}`,
        description: conv.messages?.[0]?.content?.slice(0, 100) + '...' || 'No description',
        type: getProjectType(conv.settings?.category),
        lastEdited: formatDate(conv.updated_at),
        image: sandboxUrl ? `${sandboxUrl}/preview` : null,
        reviews: 0,
        isPublic: false,
        sessionId: conv.session_id,
        sandboxUrl: sandboxUrl,
        messageCount: conv.messages?.length || 0
      }
    })

    return NextResponse.json({ projects })
  } catch (error) {
    console.error('Error fetching conversations:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function DELETE(request) {
  try {
    const session = await getServerSession()
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const sessionId = searchParams.get('sessionId')
    
    if (!sessionId) {
      return NextResponse.json({ error: 'Session ID is required' }, { status: 400 })
    }

    const result = await deleteConversation(sessionId)
    
    if (!result.success) {
      return NextResponse.json({ error: result.error || 'Failed to delete conversation' }, { status: 500 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting conversation:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

function getProjectType(category) {
  const typeMap = {
    'medical-aesthetics': 'Website',
    'dental': 'Website', 
    'functional-medicine': 'Website'
  }
  return typeMap[category] || 'Website'
}

function formatDate(date) {
  if (!date) return 'Unknown'
  
  const now = new Date()
  const diffTime = Math.abs(now - new Date(date))
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 1) return '1 day ago'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`
  return `${Math.ceil(diffDays / 30)} months ago`
}
