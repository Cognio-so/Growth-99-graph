import { connectToDatabase } from '@/lib/db'


export const ConversationSchema = {
  _id: String, 
  session_id: String, 
  title: String, 
  created_at: Date,
  updated_at: Date,
  user_id: String, 
  messages: [
    {
      id: String, 
      role: String, 
      content: String, 
      created_at: Date,
      
      conversation_id: String, 
      sandbox_url: String, 
      generated_code: String, 
      metadata: {
        model_used: String,
        generation_time: Number,
        backend_state: Object, 
      }
    }
  ],
  settings: {
    model: String,
    category: String,
  },
  status: String, 
}


export class ConversationService {
  static async createConversation(sessionId, userId, initialMessage) {
    const { db } = await connectToDatabase()
    
    const conversation = {
      session_id: sessionId,
      title: this.generateTitle(initialMessage),
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
    return { ...conversation, _id: result.insertedId }
  }

  static async addMessage(sessionId, message) {
    const { db } = await connectToDatabase()
    
    const messageId = `m${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const messageWithId = {
      ...message,
      id: messageId,
      created_at: new Date()
    }
    
    await db.collection('conversations').updateOne(
      { session_id: sessionId },
      { 
        $push: { messages: messageWithId },
        $set: { updated_at: new Date() }
      }
    )
    
    return messageWithId
  }

  static async updateAssistantMessage(sessionId, messageId, updates) {
    const { db } = await connectToDatabase()
    
    await db.collection('conversations').updateOne(
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
  }

  static async getConversation(sessionId) {
    const { db } = await connectToDatabase()
    return await db.collection('conversations').findOne({ session_id: sessionId })
  }

  static async getUserConversations(userId, limit = 20) {
    const { db } = await connectToDatabase()
    return await db.collection('conversations')
      .find({ user_id: userId, status: 'active' })
      .sort({ updated_at: -1 })
      .limit(limit)
      .toArray()
  }

  static generateTitle(message) {
    const words = message.split(' ').slice(0, 6)
    return words.join(' ') + (message.split(' ').length > 6 ? '...' : '')
  }
}
