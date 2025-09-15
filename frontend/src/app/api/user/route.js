import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { 
  getCurrentUser, 
  updateCurrentUser, 
  getUserStats,
  incrementUserQueries 
} from '@/lib/actions/user-actions';

// GET - Get current user data
export async function GET() {
  try {
    const result = await getCurrentUser();
    
    if (!result.success) {
      return NextResponse.json(
        { error: result.error },
        { status: result.error === 'User not authenticated' ? 401 : 500 }
      );
    }
    
    return NextResponse.json({ user: result.user });
  } catch (error) {
    console.error('Error in GET /api/user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// PUT - Update current user data
export async function PUT(request) {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return NextResponse.json(
        { error: 'User not authenticated' },
        { status: 401 }
      );
    }
    
    const updateData = await request.json();
    
    // Remove sensitive fields that shouldn't be updated via this endpoint
    const allowedFields = [
      'firstName', 
      'lastName', 
      'username', 
      'preferences'
    ];
    
    const filteredData = {};
    for (const field of allowedFields) {
      if (updateData[field] !== undefined) {
        filteredData[field] = updateData[field];
      }
    }
    
    const result = await updateCurrentUser(filteredData);
    
    if (!result.success) {
      return NextResponse.json(
        { error: result.error },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ 
      success: true, 
      message: 'User updated successfully' 
    });
  } catch (error) {
    console.error('Error in PUT /api/user:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
