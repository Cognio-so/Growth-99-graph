import { NextRequest, NextResponse } from 'next/server'

export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const error = searchParams.get('error')

  if (error) {
    // User denied authorization
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>GitHub Authentication</title>
        </head>
        <body>
          <script>
            window.opener?.postMessage({
              type: 'GITHUB_AUTH_RESULT',
              success: false,
              error: 'GitHub authentication was denied'
            }, window.location.origin);
            window.close();
          </script>
          <p>Authentication was denied. You can close this window.</p>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    })
  }

  if (!code) {
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>GitHub Authentication</title>
        </head>
        <body>
          <script>
            window.opener?.postMessage({
              type: 'GITHUB_AUTH_RESULT',
              success: false,
              error: 'No authorization code received'
            }, window.location.origin);
            window.close();
          </script>
          <p>No authorization code received. You can close this window.</p>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    })
  }

  try {
    // Exchange code for access token
    const tokenResponse = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        client_id: process.env.GITHUB_CLIENT_ID,
        client_secret: process.env.GITHUB_CLIENT_SECRET,
        code: code,
      }),
    })

    const tokenData = await tokenResponse.json()

    if (tokenData.error) {
      return new Response(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>GitHub Authentication</title>
          </head>
          <body>
            <script>
              window.opener?.postMessage({
                type: 'GITHUB_AUTH_RESULT',
                success: false,
                error: 'Token exchange failed: ${tokenData.error_description}'
              }, window.location.origin);
              window.close();
            </script>
            <p>Token exchange failed. You can close this window.</p>
          </body>
        </html>
      `, {
        headers: { 'Content-Type': 'text/html' }
      })
    }

    // Send success message to parent window
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>GitHub Authentication</title>
        </head>
        <body>
          <script>
            window.opener?.postMessage({
              type: 'GITHUB_AUTH_RESULT',
              success: true,
              accessToken: '${tokenData.access_token}'
            }, window.location.origin);
            window.close();
          </script>
          <p>Authentication successful! You can close this window.</p>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    })

  } catch (error) {
    console.error('GitHub OAuth callback error:', error)
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>GitHub Authentication</title>
        </head>
        <body>
          <script>
            window.opener?.postMessage({
              type: 'GITHUB_AUTH_RESULT',
              success: false,
              error: 'OAuth callback failed'
            }, window.location.origin);
            window.close();
          </script>
          <p>Authentication failed. You can close this window.</p>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    })
  }
}
