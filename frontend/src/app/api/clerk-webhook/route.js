import { headers } from 'next/headers'
import { Webhook } from 'svix'
import { prisma } from '@/lib/db'

export async function POST(req) {
  // Get the headers
  const headerPayload = headers()
  const svix_id = headerPayload.get('svix-id')
  const svix_timestamp = headerPayload.get('svix-timestamp')
  const svix_signature = headerPayload.get('svix-signature')

  // If there are no headers, error out
  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response('Error occured -- no svix headers', {
      status: 400,
    })
  }

  // Get the body
  const payload = await req.json()
  const body = JSON.stringify(payload)

  // Create a new Svix instance with your secret.
  const wh = new Webhook(process.env.CLERK_WEBHOOK_SECRET || '')

  let evt

  // Verify the payload with the headers
  try {
    evt = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    })
  } catch (err) {
    console.error('Error verifying webhook:', err)
    return new Response('Error occured', {
      status: 400,
    })
  }

  // Get the ID and type
  const { id } = evt.data
  const eventType = evt.type

  console.log(`Webhook with an ID of ${id} and type of ${eventType}`)
  console.log('Webhook body:', body)

  // Handle the webhook
  if (eventType === 'user.created') {
    const { id, email_addresses, first_name, last_name, image_url } = evt.data

    // Get the primary email address
    const primaryEmail = email_addresses.find(email => email.id === evt.data.primary_email_address_id)
    
    if (primaryEmail) {
      try {
        await prisma.user.create({
          data: {
            id: id,
            email: primaryEmail.email_address,
            name: first_name && last_name ? `${first_name} ${last_name}` : first_name || last_name || null,
            imageUrl: image_url || null,
          },
        })
        
        console.log(`User created: ${id}`)
      } catch (error) {
        console.error('Error creating user:', error)
        return new Response('Error creating user', { status: 500 })
      }
    }
  }

  if (eventType === 'user.updated') {
    const { id, email_addresses, first_name, last_name, image_url } = evt.data

    // Get the primary email address
    const primaryEmail = email_addresses.find(email => email.id === evt.data.primary_email_address_id)
    
    if (primaryEmail) {
      try {
        await prisma.user.upsert({
          where: { id: id },
          update: {
            email: primaryEmail.email_address,
            name: first_name && last_name ? `${first_name} ${last_name}` : first_name || last_name || null,
            imageUrl: image_url || null,
            updatedAt: new Date(),
          },
          create: {
            id: id,
            email: primaryEmail.email_address,
            name: first_name && last_name ? `${first_name} ${last_name}` : first_name || last_name || null,
            imageUrl: image_url || null,
          },
        })
        
        console.log(`User updated: ${id}`)
      } catch (error) {
        console.error('Error updating user:', error)
        return new Response('Error updating user', { status: 500 })
      }
    }
  }

  if (eventType === 'user.deleted') {
    try {
      await prisma.user.delete({
        where: { id: id },
      })
      
      console.log(`User deleted: ${id}`)
    } catch (error) {
      console.error('Error deleting user:', error)
      return new Response('Error deleting user', { status: 500 })
    }
  }

  return new Response('', { status: 200 })
}
