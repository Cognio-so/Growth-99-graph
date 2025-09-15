import { headers } from "next/headers";
import { Webhook } from "svix";
import { connectDB } from "@/lib/db";
import User from "@/models/UserModel";

export async function POST(req) {
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

  // If there are no headers, error out
  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response("Error: missing svix headers", {
      status: 400,
    });
  }

  // Get the body
  const payload = await req.json();
  const body = JSON.stringify(payload);

  // Create a new Svix instance with your secret.
  const wh = new Webhook(WEBHOOK_SECRET);

  let evt;

  // Verify the payload with the headers
  try {
    evt = wh.verify(body, {
      "svix-id": svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    });
  } catch (err) {
    console.error("Error verifying webhook:", err);
    return new Response("Error: could not verify webhook", {
      status: 400,
    });
  }

  // Get the ID and type
  const { id } = evt.data;
  const eventType = evt.type;

  console.log(`Webhook with an ID of ${id} and type of ${eventType}`);

  // Connect to the database
  await connectDB();

  try {
    if (eventType === "user.created") {
      const {
        id,
        email_addresses,
        first_name,
        last_name,
        image_url,
      } = evt.data;
      const email = email_addresses[0]?.email_address;

      if (!email) {
        return new Response("Error: missing user email", { status: 400 });
      }

      const newUser = new User({
        clerkId: id,
        name: `${first_name || ""} ${last_name || ""}`.trim(),
        email,
        firstName: first_name || "",
        lastName: last_name || "",
        profileImage: image_url || "",
        role: "user",
        status: "active",
      });

      await newUser.save();
      console.log(`User ${id} was created in the database.`);
      return new Response("User created successfully", { status: 201 });
    }

    if (eventType === "user.updated") {
      const {
        id,
        email_addresses,
        first_name,
        last_name,
        image_url,
      } = evt.data;
      const email = email_addresses[0]?.email_address;

      if (!email) {
        return new Response("Error: missing user email", { status: 400 });
      }

      const updatedUser = await User.findOneAndUpdate(
        { clerkId: id },
        {
          name: `${first_name || ""} ${last_name || ""}`.trim(),
          email,
          firstName: first_name || "",
          lastName: last_name || "",
          profileImage: image_url || "",
        },
        { new: true }
      );

      if (!updatedUser) {
        return new Response("Error: user not found", { status: 404 });
      }

      console.log(`User ${id} was updated in the database.`);
      return new Response("User updated successfully", { status: 200 });
    }

    if (eventType === "user.deleted") {
      const { id } = evt.data;
      const deletedUser = await User.findOneAndDelete({ clerkId: id });

      if (!deletedUser) {
        return new Response("Error: user not found", { status: 404 });
      }

      console.log(`User ${id} was deleted from the database.`);
      return new Response("User deleted successfully", { status: 200 });
    }

    return new Response("", { status: 200 });
  } catch (error) {
    console.error("Error processing webhook:", error);
    return new Response("Internal server error", { status: 500 });
  }
}