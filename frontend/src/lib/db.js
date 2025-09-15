import { MongoClient } from "mongodb";

const uri = process.env.MONGODB_URI ;
const dbName = process.env.MONGODB_DB_NAME ;

let client;
let db;

export async function connectToDatabase() {
  if (client && db) {
    return { client, db };
  }

  // Validate environment variables
  if (!uri) {
    throw new Error("MONGODB_URI environment variable is required");
  }

  if (!dbName) {
    throw new Error("MONGODB_DB_NAME environment variable is required");
  }

  try {
    // Add connection options for better timeout handling
    const options = {
      serverSelectionTimeoutMS: 30000, // 30 seconds
      connectTimeoutMS: 30000, // 30 seconds
      socketTimeoutMS: 30000, // 30 seconds
      maxPoolSize: 10, // Maintain up to 10 socket connections
      retryWrites: true,
      w: 'majority'
    };

    client = new MongoClient(uri, options);
    await client.connect();
    db = client.db(dbName);
    
    console.log("Connected to MongoDB successfully");
    return { client, db };
  } catch (error) {
    console.error("Failed to connect to MongoDB:", error);
    throw error;
  }
}

export { db };