import { headers } from "next/headers";
import { Webhook } from "svix";
import { connectToDatabase } from "@/lib/db";
import { createUserDocument, updateUserDocument } from "@/models/user";

// Add GET method for testing
export async function GET() {
  return new Response("Webhook endpoint is working - GET method", { 
    status: 200,
    headers: {
      'Content-Type': 'text/plain'
    }
  });
}

export async function POST(req) {
  console.log("=== WEBHOOK POST RECEIVED ===");
  
  // Get the webhook secret from environment variables
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

  if (!WEBHOOK_SECRET) {
    console.error("Clerk webhook secret not found in environment variables.");
    return new Response("Webhook secret not configured", { status: 500 });
  }

  // Get the headers
  const headerPayload = headers();
  const svix_id = headerPayload.get("svix-id");
  const svix_timestamp = headerPayload.get("svix-timestamp");
  const svix_signature = headerPayload.get("svix-signature");

  console.log("Headers received:", {
    svix_id: svix_id ? 'present' : 'missing',
    svix_timestamp: svix_timestamp ? 'present' : 'missing', 
    svix_signature: svix_signature ? 'present' : 'missing'
  });

  // If there are no headers, error out
  if (!svix_id || !svix_timestamp || !svix_signature) {
    console.error("Missing svix headers");
    return new Response("Error: missing svix headers", {
      status: 400,
    });
  }

  // Get the body
  const payload = await req.text();
  const body = JSON.parse(payload);

  console.log("Webhook payload type:", body.type);
  console.log("Webhook payload data ID:", body.data?.id);

  // Create a new Svix instance with your secret.
  const wh = new Webhook(WEBHOOK_SECRET);

  let evt;

  // Verify the payload with the headers
  try {
    evt = wh.verify(payload, {
      "svix-id": svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    });
    console.log("Webhook verification successful");
  } catch (err) {
    console.error("Error verifying webhook:", err);
    return new Response("Error: could not verify webhook", {
      status: 400,
    });
  }

  // Get the ID and type
  const { id } = evt.data;
  const eventType = evt.type;

  console.log(`Processing webhook - ID: ${id}, Type: ${eventType}`);

  // Connect to the database
  try {
    const { db } = await connectToDatabase();
    const usersCollection = db.collection('users');

    if (eventType === "user.created") {
      const userDoc = createUserDocument(evt.data);
      await usersCollection.insertOne(userDoc);
      console.log(`✅ User ${id} was created in the database.`);
      return new Response("User created successfully", { status: 201 });
    }

    if (eventType === "user.updated") {
      const existingUser = await usersCollection.findOne({ clerkId: id });
      if (existingUser) {
        const updatedUser = updateUserDocument(existingUser, evt.data);
        await usersCollection.updateOne(
          { clerkId: id },
          { $set: updatedUser }
        );
        console.log(`✅ User ${id} was updated in the database.`);
        return new Response("User updated successfully", { status: 200 });
      } else {
        // If user doesn't exist, create them
        const userDoc = createUserDocument(evt.data);
        await usersCollection.insertOne(userDoc);
        console.log(`✅ User ${id} was created in the database (from update).`);
        return new Response("User created successfully", { status: 201 });
      }
    }

    if (eventType === "user.deleted") {
      const result = await usersCollection.deleteOne({ clerkId: id });
      if (result.deletedCount > 0) {
        console.log(`✅ User ${id} was deleted from the database.`);
        return new Response("User deleted successfully", { status: 200 });
      } else {
        console.log(`ℹ️ User ${id} was not found in the database.`);
        return new Response("User not found", { status: 404 });
      }
    }

    console.log(`ℹ️ Unhandled event type: ${eventType}`);
    return new Response("Event type not handled", { status: 200 });
  } catch (error) {
    console.error("❌ Error processing webhook:", error);
    return new Response("Internal server error", { status: 500 });
  }
}