
export const UserSchema = {
  id: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  emailVerified: { type: Boolean, default: false },
  image: { type: String },
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

export const createUserDocument = (betterAuthUser) => {
  return {
    id: betterAuthUser.id,
    name: betterAuthUser.name || '',
    email: betterAuthUser.email || '',
    emailVerified: betterAuthUser.emailVerified || false,
    image: betterAuthUser.image || '',
    createdAt: new Date(betterAuthUser.createdAt || Date.now()),
    updatedAt: new Date(),
    lastSignInAt: new Date(betterAuthUser.lastSignInAt || Date.now()),
    preferences: {
      theme: 'system',
      notifications: true
    },
    totalQueries: 0,
    lastActiveAt: new Date()
  };
};

export const updateUserDocument = (existingUser, betterAuthUser) => {
  return {
    ...existingUser,
    name: betterAuthUser.name || existingUser.name,
    email: betterAuthUser.email || existingUser.email,
    emailVerified: betterAuthUser.emailVerified || existingUser.emailVerified,
    image: betterAuthUser.image || existingUser.image,
    updatedAt: new Date(),
    lastSignInAt: new Date(betterAuthUser.lastSignInAt || existingUser.lastSignInAt)
  };
};
