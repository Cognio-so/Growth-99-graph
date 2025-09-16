import { NextRequest, NextResponse } from 'next/server'

export async function POST(request) {
  try {
    const formData = await request.formData()
    const projectFiles = formData.get('projectFiles')
    const repoName = formData.get('repoName')
    const description = formData.get('description')
    const isPrivate = formData.get('isPrivate')
    const accessToken = formData.get('accessToken')

    if (!projectFiles || !repoName || !accessToken) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    console.log('Creating GitHub repository...')
    
    // Create GitHub repository
    const repoResponse = await fetch('https://api.github.com/user/repos', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: repoName,
        description: description || 'Generated React app from Growth-99-graph',
        private: isPrivate === 'true',
        auto_init: false
      })
    })

    if (!repoResponse.ok) {
      const errorData = await repoResponse.json()
      console.error('Repository creation failed:', errorData)
      return NextResponse.json(
        { error: `Failed to create repository: ${errorData.message}` },
        { status: 400 }
      )
    }

    const repoData = await repoResponse.json()
    const repoUrl = repoData.html_url
    const fullRepoName = repoData.full_name

    console.log(`Repository created: ${fullRepoName}`)

    // Extract and upload files to GitHub
    const uploadResult = await uploadFilesToGitHub(projectFiles, fullRepoName, accessToken)

    return NextResponse.json({
      success: true,
      repoUrl: repoUrl,
      filesUploaded: uploadResult.filesUploaded,
      totalFiles: uploadResult.totalFiles,
      errors: uploadResult.errors
    })

  } catch (error) {
    console.error('Deployment error:', error)
    return NextResponse.json(
      { error: `Deployment failed: ${error.message}` },
      { status: 500 }
    )
  }
}

async function uploadFilesToGitHub(projectFiles, fullRepoName, accessToken) {
  try {
    console.log('Starting file upload to GitHub...')
    console.log('Repository:', fullRepoName)
    
    // Convert blob to buffer
    const arrayBuffer = await projectFiles.arrayBuffer()
    const buffer = Buffer.from(arrayBuffer)
    
    // Extract ZIP file
    const JSZip = (await import('jszip')).default
    const zip = await JSZip.loadAsync(buffer)
    
    let filesUploaded = 0
    const errors = []
    const filesToUpload = []
    
    console.log('Processing ZIP contents...')
    
    // Process all files and prepare for upload
    for (const [relativePath, zipEntry] of Object.entries(zip.files)) {
      if (zipEntry.dir) continue // Skip directories
      
      try {
        const content = await zipEntry.async('base64')
        
        // Handle file path - remove root folder if it exists
        let filePath = relativePath
        const pathParts = relativePath.split('/')
        
        // Remove common root folder names
        if (pathParts.length > 1 && (pathParts[0] === 'my-app' || pathParts[0] === 'app' || pathParts[0] === 'project')) {
          filePath = pathParts.slice(1).join('/')
        }
        
        // Skip empty paths or hidden files
        if (!filePath || filePath === '' || filePath.startsWith('.')) continue
        
        filesToUpload.push({
          path: filePath,
          content: content,
          originalPath: relativePath
        })
        
        console.log(`Prepared: ${filePath} (from ${relativePath})`)
        
      } catch (error) {
        console.error(`Error processing file ${relativePath}:`, error)
        errors.push(`Failed to process ${relativePath}: ${error.message}`)
      }
    }
    
    console.log(`Prepared ${filesToUpload.length} files for upload`)
    
    if (filesToUpload.length === 0) {
      throw new Error('No files found to upload')
    }
    
    // Upload files sequentially with proper error handling
    for (let i = 0; i < filesToUpload.length; i++) {
      const file = filesToUpload[i]
      
      try {
        console.log(`[${i + 1}/${filesToUpload.length}] Uploading: ${file.path}`)
        
        const response = await fetch(`https://api.github.com/repos/${fullRepoName}/contents/${encodeURIComponent(file.path)}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'Growth-99-graph-Deployer/1.0'
          },
          body: JSON.stringify({
            message: `Add ${file.path}`,
            content: file.content,
            branch: 'main'
          })
        })
        
        if (response.ok) {
          const result = await response.json()
          console.log(`✅ Successfully uploaded: ${file.path}`)
          filesUploaded++
        } else {
          const errorData = await response.json()
          const errorMsg = `Failed to upload ${file.path}: ${errorData.message || response.statusText}`
          console.error(`❌ ${errorMsg}`)
          errors.push(errorMsg)
        }
        
        // Rate limiting protection
        if (i < filesToUpload.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 200))
        }
        
      } catch (error) {
        const errorMsg = `Error uploading ${file.path}: ${error.message}`
        console.error(`❌ ${errorMsg}`)
        errors.push(errorMsg)
      }
    }
    
    console.log(`Upload completed. ${filesUploaded}/${filesToUpload.length} files uploaded successfully.`)
    
    if (errors.length > 0) {
      console.log('Errors encountered:', errors)
    }
    
    return {
      filesUploaded,
      totalFiles: filesToUpload.length,
      errors
    }
    
  } catch (error) {
    console.error('Error in uploadFilesToGitHub:', error)
    throw error
  }
}
