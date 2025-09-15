import { connectToDatabase } from '@/lib/db';
import { auth } from '@clerk/nextjs/server';

// Create a new user
export async function createUser(userData) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const result = await usersCollection.insertOne({
      ...userData,
      createdAt: new Date(),
      updatedAt: new Date()
    });
    
    return { success: true, userId: result.insertedId };
  } catch (error) {
    console.error('Error creating user:', error);
    return { success: false, error: error.message };
  }
}

// Get user by Clerk ID
export async function getUserByClerkId(clerkId) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const user = await usersCollection.findOne({ clerkId });
    return { success: true, user };
  } catch (error) {
    console.error('Error getting user:', error);
    return { success: false, error: error.message };
  }
}

// Get current authenticated user
export async function getCurrentUser() {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return { success: false, error: 'User not authenticated' };
    }
    
    return await getUserByClerkId(userId);
  } catch (error) {
    console.error('Error getting current user:', error);
    return { success: false, error: error.message };
  }
}

// Update user
export async function updateUser(clerkId, updateData) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const result = await usersCollection.updateOne(
      { clerkId },
      { 
        $set: {
          ...updateData,
          updatedAt: new Date()
        }
      }
    );
    
    if (result.matchedCount === 0) {
      return { success: false, error: 'User not found' };
    }
    
    return { success: true, modifiedCount: result.modifiedCount };
  } catch (error) {
    console.error('Error updating user:', error);
    return { success: false, error: error.message };
  }
}

// Update current user
export async function updateCurrentUser(updateData) {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return { success: false, error: 'User not authenticated' };
    }
    
    return await updateUser(userId, updateData);
  } catch (error) {
    console.error('Error updating current user:', error);
    return { success: false, error: error.message };
  }
}

// Delete user
export async function deleteUser(clerkId) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const result = await usersCollection.deleteOne({ clerkId });
    
    if (result.deletedCount === 0) {
      return { success: false, error: 'User not found' };
    }
    
    return { success: true, deletedCount: result.deletedCount };
  } catch (error) {
    console.error('Error deleting user:', error);
    return { success: false, error: error.message };
  }
}

// Increment user query count
export async function incrementUserQueries(clerkId) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const result = await usersCollection.updateOne(
      { clerkId },
      { 
        $inc: { totalQueries: 1 },
        $set: { 
          lastActiveAt: new Date(),
          updatedAt: new Date()
        }
      }
    );
    
    return { success: true, modifiedCount: result.modifiedCount };
  } catch (error) {
    console.error('Error incrementing user queries:', error);
    return { success: false, error: error.message };
  }
}

// Get user statistics
export async function getUserStats(clerkId) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const user = await usersCollection.findOne(
      { clerkId },
      { 
        projection: { 
          totalQueries: 1, 
          lastActiveAt: 1, 
          createdAt: 1,
          firstName: 1,
          lastName: 1
        }
      }
    );
    
    if (!user) {
      return { success: false, error: 'User not found' };
    }
    
    return { success: true, stats: user };
  } catch (error) {
    console.error('Error getting user stats:', error);
    return { success: false, error: error.message };
  }
}

// Get all users (admin function)
export async function getAllUsers(limit = 50, skip = 0) {
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');
    
    const users = await usersCollection
      .find({})
      .sort({ createdAt: -1 })
      .limit(limit)
      .skip(skip)
      .toArray();
    
    const total = await usersCollection.countDocuments();
    
    return { 
      success: true, 
      users, 
      total,
      hasMore: skip + users.length < total
    };
  } catch (error) {
    console.error('Error getting all users:', error);
    return { success: false, error: error.message };
  }
}