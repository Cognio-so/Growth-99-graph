import { ObjectId } from 'mongodb';

export const UserSchema = {
  clerkId: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  firstName: { type: String },
  lastName: { type: String },
  username: { type: String },
  imageUrl: { type: String },
  hasImage: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
  lastSignInAt: { type: Date },
  // Additional fields you might want
  preferences: {
    theme: { type: String, default: 'system' },
    notifications: { type: Boolean, default: true }
  },
  // Track user activity
  totalQueries: { type: Number, default: 0 },
  lastActiveAt: { type: Date, default: Date.now }
};

export const createUserDocument = (clerkUser) => {
  return {
    clerkId: clerkUser.id,
    email: clerkUser.emailAddresses?.[0]?.emailAddress || '',
    firstName: clerkUser.firstName || '',
    lastName: clerkUser.lastName || '',
    username: clerkUser.username || '',
    imageUrl: clerkUser.imageUrl || '',
    hasImage: !!clerkUser.imageUrl,
    createdAt: new Date(clerkUser.createdAt),
    updatedAt: new Date(),
    lastSignInAt: new Date(clerkUser.lastSignInAt || Date.now()),
    preferences: {
      theme: 'system',
      notifications: true
    },
    totalQueries: 0,
    lastActiveAt: new Date()
  };
};

export const updateUserDocument = (existingUser, clerkUser) => {
  return {
    ...existingUser,
    email: clerkUser.emailAddresses?.[0]?.emailAddress || existingUser.email,
    firstName: clerkUser.firstName || existingUser.firstName,
    lastName: clerkUser.lastName || existingUser.lastName,
    username: clerkUser.username || existingUser.username,
    imageUrl: clerkUser.imageUrl || existingUser.imageUrl,
    hasImage: !!clerkUser.imageUrl || existingUser.hasImage,
    updatedAt: new Date(),
    lastSignInAt: new Date(clerkUser.lastSignInAt || existingUser.lastSignInAt)
  };
};
