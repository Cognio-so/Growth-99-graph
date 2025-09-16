'use server';
import { connectToDatabase } from '@/lib/db';
import { getServerSession } from '@/lib/get-session';

// Get current user data
export async function getCurrentUser() {
  try {
    const session = await getServerSession();
    
    if (!session?.user) {
      return { success: false, error: 'User not authenticated' };
    }

    const { db } = await connectToDatabase();
    const user = await db.collection('users').findOne({ 
      id: session.user.id 
    });

    if (!user) {
      return { success: false, error: 'User not found' };
    }

    // Remove sensitive data
    const { password, ...userWithoutPassword } = user;
    
    return { success: true, user: userWithoutPassword };
  } catch (error) {
    console.error('Error getting current user:', error);
    return { success: false, error: 'Internal server error' };
  }
}

// Update current user data
export async function updateCurrentUser(updateData) {
  try {
    const session = await getServerSession();
    
    if (!session?.user) {
      return { success: false, error: 'User not authenticated' };
    }

    const { db } = await connectToDatabase();
    
    // Add updatedAt timestamp
    const dataToUpdate = {
      ...updateData,
      updatedAt: new Date()
    };

    const result = await db.collection('users').updateOne(
      { id: session.user.id },
      { $set: dataToUpdate }
    );

    if (result.matchedCount === 0) {
      return { success: false, error: 'User not found' };
    }

    return { success: true, message: 'User updated successfully' };
  } catch (error) {
    console.error('Error updating user:', error);
    return { success: false, error: 'Internal server error' };
  }
}

// Get user statistics
export async function getUserStats() {
  try {
    const session = await getServerSession();
    
    if (!session?.user) {
      return { success: false, error: 'User not authenticated' };
    }

    const { db } = await connectToDatabase();
    const user = await db.collection('users').findOne({ 
      id: session.user.id 
    });

    if (!user) {
      return { success: false, error: 'User not found' };
    }

    const stats = {
      totalQueries: user.totalQueries || 0,
      createdAt: user.createdAt,
      lastActiveAt: user.lastActiveAt
    };

    return { success: true, stats };
  } catch (error) {
    console.error('Error getting user stats:', error);
    return { success: false, error: 'Internal server error' };
  }
}

// Increment user query count
export async function incrementUserQueries() {
  try {
    const session = await getServerSession();
    
    if (!session?.user) {
      return { success: false, error: 'User not authenticated' };
    }

    const { db } = await connectToDatabase();
    
    const result = await db.collection('users').updateOne(
      { id: session.user.id },
      { 
        $inc: { totalQueries: 1 },
        $set: { lastActiveAt: new Date() }
      }
    );

    if (result.matchedCount === 0) {
      return { success: false, error: 'User not found' };
    }

    return { success: true };
  } catch (error) {
    console.error('Error incrementing user queries:', error);
    return { success: false, error: 'Internal server error' };
  }
}

// Delete user account
export async function deleteUserAccount() {
  try {
    const session = await getServerSession();
    
    if (!session?.user) {
      return { success: false, error: 'User not authenticated' };
    }

    const { db } = await connectToDatabase();
    
    // Delete user data
    const result = await db.collection('users').deleteOne({ 
      id: session.user.id 
    });

    if (result.deletedCount === 0) {
      return { success: false, error: 'User not found' };
    }

    return { success: true, message: 'Account deleted successfully' };
  } catch (error) {
    console.error('Error deleting user account:', error);
    return { success: false, error: 'Internal server error' };
  }
}