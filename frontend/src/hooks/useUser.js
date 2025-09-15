'use client';

import { useUser as useClerkUser } from '@clerk/nextjs';
import { useState, useEffect } from 'react';

export function useUser() {
  const { user: clerkUser, isLoaded, isSignedIn } = useClerkUser();
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      fetchUserData();
    } else if (isLoaded && !isSignedIn) {
      setUserData(null);
      setLoading(false);
    }
  }, [isLoaded, isSignedIn]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/user');
      
      if (response.ok) {
        const data = await response.json();
        setUserData(data.user);
        setError(null);
      } else {
        const errorData = await response.json();
        setError(errorData.error);
      }
    } catch (err) {
      setError('Failed to fetch user data');
      console.error('Error fetching user data:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateUser = async (updateData) => {
    try {
      const response = await fetch('/api/user', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        await fetchUserData(); // Refresh user data
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (err) {
      return { success: false, error: 'Failed to update user' };
    }
  };

  const incrementQueries = async () => {
    try {
      const response = await fetch('/api/user/stats', {
        method: 'POST',
      });

      if (response.ok) {
        await fetchUserData(); // Refresh user data
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (err) {
      return { success: false, error: 'Failed to increment queries' };
    }
  };

  return {
    // Clerk user data
    clerkUser,
    isLoaded,
    isSignedIn,
    
    // MongoDB user data
    userData,
    loading,
    error,
    
    // Actions
    updateUser,
    incrementQueries,
    refreshUser: fetchUserData,
  };
}