"use server"

import { connectToDatabase } from '@/lib/db'

// Generate message ID
function generateMessageId() {
  return `m${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Generate conversation title
function generateTitle(message) {
  const words = message.split(' ').slice(0, 6)
  return words.join(' ') + (message.split(' ').length > 6 ? '...' : '')
}

// Serialize MongoDB document to plain object
function serializeDocument(doc) {
  if (!doc) return null
  
  const serialized = {
    _id: doc._id?.toString(),
    session_id: doc.session_id,
    title: doc.title,
    created_at: doc.created_at,
    updated_at: doc.updated_at,
    user_id: doc.user_id,
    messages: doc.messages?.map(msg => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      created_at: msg.created_at,
      conversation_id: msg.conversation_id,
      sandbox_url: msg.sandbox_url,
      generated_code: msg.generated_code,
      metadata: msg.metadata
    })) || [],
    settings: doc.settings,
    status: doc.status
  }
  
  return serialized
}

// Create a new conversation
export async function createConversation(sessionId, userId, initialMessage) {
  try {
    const { db } = await connectToDatabase()
    
    // Check if conversation already exists
    const existingConversation = await db.collection('conversations').findOne({ session_id: sessionId })
    if (existingConversation) {
      return { success: true, data: serializeDocument(existingConversation) }
    }
    
    const conversation = {
      session_id: sessionId,
      title: generateTitle(initialMessage),
      created_at: new Date(),
      updated_at: new Date(),
      user_id: userId,
      messages: [],
      settings: {
        model: 'gpt-oss-120b',
        category: 'medical-aesthetics'
      },
      status: 'active'
    }
    
    const result = await db.collection('conversations').insertOne(conversation)
    const createdDoc = await db.collection('conversations').findOne({ _id: result.insertedId })
    
    return { success: true, data: serializeDocument(createdDoc) }
  } catch (error) {
    console.error('Error creating conversation:', error)
    return { success: false, error: error.message }
  }
}

// Add a message to conversation
export async function addMessage(sessionId, message) {
  try {
    const { db } = await connectToDatabase()
    
    const messageId = generateMessageId()
    const messageWithId = {
      ...message,
      id: messageId,
      created_at: new Date()
    }
    
    // Check if conversation exists
    const conversation = await db.collection('conversations').findOne({ session_id: sessionId })
    if (!conversation) {
      console.error('Conversation not found for session:', sessionId)
      return { success: false, error: 'Conversation not found' }
    }
    
    // Add message to conversation
    const result = await db.collection('conversations').updateOne(
      { session_id: sessionId },
      { 
        $push: { messages: messageWithId },
        $set: { updated_at: new Date() }
      }
    )
    
    if (result.modifiedCount === 0) {
      console.error('Failed to add message to conversation')
      return { success: false, error: 'Failed to add message' }
    }
    
    return { success: true, data: messageWithId }
  } catch (error) {
    console.error('Error adding message:', error)
    return { success: false, error: error.message }
  }
}

// Update assistant message with backend data
export async function updateAssistantMessage(sessionId, messageId, updates) {
  try {
    const { db } = await connectToDatabase()
    
    const result = await db.collection('conversations').updateOne(
      { 
        session_id: sessionId,
        'messages.id': messageId
      },
      { 
        $set: { 
          'messages.$.conversation_id': updates.conversation_id,
          'messages.$.sandbox_url': updates.sandbox_url,
          'messages.$.generated_code': updates.generated_code,
          'messages.$.metadata': updates.metadata,
          updated_at: new Date()
        }
      }
    )
    
    if (result.modifiedCount === 0) {
      console.error('Failed to update assistant message')
      return { success: false, error: 'Failed to update message' }
    }
    
    return { success: true }
  } catch (error) {
    console.error('Error updating assistant message:', error)
    return { success: false, error: error.message }
  }
}

// Get conversation by session ID
export async function getConversation(sessionId) {
  try {
    const { db } = await connectToDatabase()
    const conversation = await db.collection('conversations').findOne({ session_id: sessionId })
    
    if (!conversation) {
      return { success: false, error: 'Conversation not found' }
    }
    
    return { success: true, data: serializeDocument(conversation) }
  } catch (error) {
    console.error('Error getting conversation:', error)
    return { success: false, error: error.message }
  }
}

// Get user conversations
export async function getUserConversations(userId, limit = 20) {
  try {
    const { db } = await connectToDatabase()
    const conversations = await db.collection('conversations')
      .find({ user_id: userId, status: 'active' })
      .sort({ updated_at: -1 })
      .limit(limit)
      .toArray()
    
    return { success: true, data: conversations.map(serializeDocument) }
  } catch (error) {
    console.error('Error getting user conversations:', error)
    return { success: false, error: error.message }
  }
}

// Delete conversation
export async function deleteConversation(sessionId) {
  try {
    const { db } = await connectToDatabase()
    const result = await db.collection('conversations').updateOne(
      { session_id: sessionId },
      { $set: { status: 'deleted', updated_at: new Date() } }
    )
    
    if (result.modifiedCount === 0) {
      return { success: false, error: 'Conversation not found' }
    }
    
    return { success: true }
  } catch (error) {
    console.error('Error deleting conversation:', error)
    return { success: false, error: error.message }
  }
}
