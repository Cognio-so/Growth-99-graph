import { betterAuth } from "better-auth";
import { mongodbAdapter } from "better-auth/adapters/mongodb";
import { connectToDatabase } from "@/lib/db";
import { sendVerificationEmail } from "./email.js";

let db;
try {
  const { db: database } = await connectToDatabase();
  db = database;
} catch (error) {
  console.error("Failed to initialize database:", error);
  throw error;
}

export const auth = betterAuth({
  database: mongodbAdapter(db),
  emailAndPassword: { 
    enabled: true
  },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    },
    github: {
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
    }
  },
  emailVerification: {
    sendOnSignUp: true,
    autoSignInAfterVerification: true,
    async sendVerificationEmail({ user, url }) {
      try {
        await sendVerificationEmail(user.email, url);
        console.log(`Verification email sent to ${user.email}`);
      } catch (error) {
        console.error("Failed to send verification email:", error);
        throw error;
      }
    }
  },
  user: {
    additionalFields: {
      role: {
        type: "string",
        input: false,
        required: false,
        defaultValue: "user", 
        validate: (value) => {
          const allowedRoles = ["admin", "user"];
          return allowedRoles.includes(value);
        }
      }
    }
  }
});

// export type Session = typeof auth.$Infer.Session;
// export type User = typeof auth.$Infer.Session.User;