import os
import re
import time
from typing import Dict, Any, Optional, List

# E2B v2.x SDK
from e2b_code_interpreter import Sandbox

# Global sandbox state - ENHANCED with session tracking
import threading
from typing import Dict, Any

# Session-based sandbox storage
_session_sandboxes: Dict[str, Dict[str, Any]] = {}
_sandbox_lock = threading.Lock()

import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
_session_exec_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

# Add at the top after imports
_executor = ThreadPoolExecutor(max_workers=10)

async def _async_sandbox_command(sandbox, command: str, timeout: int = 30):
    """Run sandbox command asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: sandbox.commands.run(command, timeout=timeout))

async def _async_sandbox_file_write(sandbox, path: str, content: str):
    """Write file asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: sandbox.files.write(path, content))

async def _async_sandbox_file_read(sandbox, path: str):
    """Read file asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: sandbox.files.read(path))

def _get_session_sandbox(session_id: str):
    """Get sandbox for a specific session."""
    with _sandbox_lock:
        return _session_sandboxes.get(session_id, {}).get("sandbox")

def _set_session_sandbox(session_id: str, sandbox, info):
    """Set sandbox for a specific session."""
    with _sandbox_lock:
        _session_sandboxes[session_id] = {"sandbox": sandbox, "info": info}

def _get_session_info(session_id: str):
    """Get sandbox info for a specific session."""
    with _sandbox_lock:
        return _session_sandboxes.get(session_id, {}).get("info", {})

def _remove_session_sandbox(session_id: str):
    """Remove sandbox for a specific session."""
    with _sandbox_lock:
        if session_id in _session_sandboxes:
            del _session_sandboxes[session_id]
# -----------------------------
# Utility: normalize generator script to current E2B API - FIXED
# -----------------------------
def _normalize_e2b_api(src: str) -> str:
    """
    Convert any legacy generator script to current E2B SDK surface.
    Also removes markdown code blocks that some LLMs add.
    """
    import re  # ✅ FIXED: Move import to top to prevent UnboundLocalError
    
    print("Normalizing the generator script for current E2B SDK...")

    # CRITICAL FIX: Remove markdown code blocks if present
    if "```python" in src:
        # Extract code between ```python and ```
        code_match = re.search(r'```python\s*(.*?)\s*```', src, re.DOTALL)
        if code_match:
            src = code_match.group(1)
            print("✅ Removed markdown code blocks from script")
    elif "```" in src:
        # Remove any other code blocks
        src = re.sub(r'```[^\n]*\n', '', src)
        src = re.sub(r'\n```', '', src)
        print("✅ Cleaned up code block markers")

    # filesystem -> files
    src = src.replace("sandbox.filesystem.", "sandbox.files.")

    # process.start_and_wait(...) -> commands.run(...)
    src = re.sub(
        r"sandbox\.process\.start_and_wait\((.*?)\)",
        r"sandbox.commands.run(\1)",
        src,
        flags=re.DOTALL,
    )

    # process.start(...) -> commands.run(..., background=True)
    src = re.sub(
        r"sandbox\.process\.start\((.*?)\)",
        r"sandbox.commands.run(\1, background=True)",
        src,
        flags=re.DOTALL,
    )

    # get_hostname -> get_host
    src = src.replace("sandbox.get_hostname", "sandbox.get_host")

    # Remove the problematic function call at the end
    if "create_react_app(None)" in src:
        src = src.replace("create_react_app(None)", "")
        print("✅ Removed problematic function call from script")

    # Also remove any other function calls that shouldn't be there
    src = re.sub(r'create_react_app\([^)]*\)\s*$', '', src, flags=re.MULTILINE)

    return src


def _get_sandbox_timeout() -> int:
    """Reads E2B_TIMEOUT and returns a safe value (1..3600)."""
    max_allowed = 3600
    default = 600
    raw = os.getenv("E2B_TIMEOUT", str(default))
    try:
        val = int(raw)
    except Exception:
        print(f"⚠️ Invalid E2B_TIMEOUT='{raw}', falling back to {default}s.")
        return default
    if val <= 0:
        print(f"⚠️ E2B_TIMEOUT={val}s is not positive, using {default}s.")
        return default
    if val > max_allowed:
        print(f"⚠️ E2B_TIMEOUT={val}s exceeds max {max_allowed}s. Capping to {max_allowed}s.")
        return max_allowed
    return val


async def _create_fast_vite_project(sandbox) -> bool:
    """Create a Vite + React project with CDN Tailwind."""
    print("Creating Vite project with optimized approach...")

    try:
        # 1) Scaffold Vite React app
        await _async_sandbox_command(sandbox, "npm create vite@latest my-app -- --template react", 180)

        # 2) Install dependencies
        await _async_sandbox_command(sandbox, "cd my-app && npm install", 300)

        # 3) Setup Tailwind with CDN approach for speed
        index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>"""
        await _async_sandbox_file_write(sandbox, "my-app/index.html", index_html)

        print("✅ Vite project created with CDN Tailwind")
        return True

    except Exception as e:
        print(f"❌ Error creating Vite project: {e}")
        return False


async def _ensure_css_files(sandbox: Sandbox):
    print("🎨 Ensuring comprehensive CSS files...")
    try:
        # Ensure index.css exists with Tailwind directives
        index_css_path = "my-app/src/index.css"
        
        # Always create a fresh index.css with proper content
        css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        await _async_sandbox_file_write(sandbox, index_css_path, css_content)
        print("✅ Created fresh index.css with Tailwind directives")
            
        # Ensure main.jsx imports index.css
        main_jsx_path = "my-app/src/main.jsx"
        main_content = await _async_sandbox_file_read(sandbox, main_jsx_path)
        if "import App from './App.jsx';" in main_content and "import './index.css'" not in main_content:
            main_content = main_content.replace(
                "import App from './App.jsx';",
                "import App from './App.jsx';\nimport './index.css';"
            )
            await _async_sandbox_file_write(sandbox, main_jsx_path, main_content)
            print("✅ Added index.css import to main.jsx")
            
    except Exception as e:
        print(f"❌ Error ensuring CSS files: {e}")

async def _ensure_tailwind_cdn_in_index_html(sandbox: Sandbox) -> bool:
    print("🎯 Ensuring Tailwind CDN in index.html...")
    try:
        path = "my-app/index.html"
        html = await _async_sandbox_file_read(sandbox, path)
    except Exception as e:
        print(f"⚠️ Could not read index.html: {e}")
        return False

    # Always inject fresh Tailwind CDN (don't check if already present)
    inject = """
  <script>
    window.tailwind = window.tailwind || {};
    window.tailwind.config = {
      theme: { extend: {} },
      darkMode: 'class',
      plugins: [],
    };
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
"""

    try:
        # Remove any existing Tailwind CDN scripts first
        html = re.sub(r'<script[^>]*cdn\.tailwindcss\.com[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<script[^>]*window\.tailwind[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        
        # Inject fresh CDN
        if "</head>" in html:
            html = html.replace("</head>", f"{inject}\n</head>")
        else:
            html = inject + "\n" + html
            
        await _async_sandbox_file_write(sandbox, path, html)
        print("✅ Injected fresh Tailwind CDN into index.html")
        return True
    except Exception as e:
        print(f"❌ Failed to write index.html: {e}")
        return False



async def _write_vite_config(sandbox, public_host: str, port: int) -> None:
    """Fixed Vite config for E2B."""
    print(f"Patching Vite config for allowed host: {public_host}")

    js_config = f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
  server: {{
    host: '0.0.0.0',
    port: {port},
    strictPort: true,
    allowedHosts: ['{public_host}', 'localhost', '127.0.0.1', /\\.e2b\\.app$/],
    hmr: false
  }},
  preview: {{
    host: '0.0.0.0',
    port: {port},
    strictPort: true
  }}
}})"""

    try:
        await _async_sandbox_file_write(sandbox, "my-app/vite.config.js", js_config)
        print("✅ Vite config patched with E2B host configuration.")
    except Exception as e:
        print(f"⚠️ Could not write vite config: {e}")


async def _wait_for_http(sandbox, port: int, max_attempts: int = 5) -> bool:  # Reduced from 30 to 5
    """Wait for HTTP server to be ready - FIXED VERSION."""
    print(f"Checking if server is ready (attempt 1/{max_attempts})...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = await _async_sandbox_command(sandbox, f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", 10)
            if result and result.stdout:
                response_code = result.stdout.strip()
                print(f"   Attempt {attempt}: HTTP response code: {response_code}")
                
                # Accept any successful HTTP response
                if response_code and response_code != "000" and response_code != "":
                    print(f"ℹ️ HTTP on :{port} responded with {response_code} - server is ready")
                    return True
        except Exception as e:
            print(f"   Attempt {attempt}: Error checking server: {e}")
        
        if attempt < max_attempts:
            await asyncio.sleep(3)
    
    print(f"❌ Server not ready after {max_attempts} attempts")
    return False


async def _start_dev_server(sandbox, port: int = 5173) -> Optional[str]:
    """Start the Vite dev server."""
    print("Starting development server (vite dev)...")

    try:
        await _async_sandbox_command(sandbox,
            f"bash -lc \"cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &\"",
        
        )

        if not await _wait_for_http(sandbox, port):
            print("⚠️ Dev server did not become ready.")
            return None

        host = sandbox.get_host(port)
        url = f"https://{host}"
        print(f"✅ Dev server started at: {url}")
        return url

    except Exception as e:
        print(f"❌ Error starting dev server: {e}")
        return None


async def _start_preview_server(sandbox, port_primary: int = 5173, port_fallback: int = 4173) -> Optional[str]:
    """Build and start Vite preview."""
    print("Starting preview server (vite preview) as fallback...")

    try:
        await _async_sandbox_command(sandbox, "cd my-app && npm run build", 480)

        await _async_sandbox_command(sandbox,
            f"bash -lc \"cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_primary} > preview.log 2>&1 &\"",
            
        )
        if await _wait_for_http(sandbox, port_primary):
            host = sandbox.get_host(port_primary)
            return f"https://{host}"

        await _async_sandbox_command(sandbox,
            f"bash -lc \"cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_fallback} > preview_fallback.log 2>&1 &\"",
        
        )
        if await _wait_for_http(sandbox, port_fallback):
            host = sandbox.get_host(port_fallback)
            return f"https://{host}"

        return None

    except Exception as e:
        print(f"❌ Error starting preview server: {e}")
        return None


async def _create_sandbox_with_timeout(timeout_s: int):
    """Create a sandbox with timeout handling asynchronously."""
    try:
        loop = asyncio.get_event_loop()
        if hasattr(Sandbox, "create"):
            template_id = os.getenv("E2B_TEMPLATE_ID")
            if template_id:
                return await loop.run_in_executor(None, lambda: Sandbox.create(template=template_id, timeout=timeout_s))
            return await loop.run_in_executor(None, lambda: Sandbox.create(timeout=timeout_s))
        return await loop.run_in_executor(None, lambda: Sandbox(timeout=timeout_s))
    except Exception as e:
        msg = str(e)
        if "Timeout cannot be greater than" in msg or "1 hours" in msg or "1 hour" in msg:
            print("⚠️ Provider rejected timeout. Retrying once with 3600s.")
            loop = asyncio.get_event_loop()
            if hasattr(Sandbox, "create"):
                template_id = os.getenv("E2B_TEMPLATE_ID")
                if template_id:
                    return await loop.run_in_executor(None, lambda: Sandbox.create(template=template_id, timeout=3600))
                return await loop.run_in_executor(None, lambda: Sandbox.create(timeout=3600))
            return await loop.run_in_executor(None, lambda: Sandbox(timeout=3600))
        raise


async def _create_fallback_react_app(sandbox) -> None:
    """Create a working fallback React app - ENHANCED VERSION."""
    print("🔧 Creating enhanced fallback React app...")
    
    # Create main.jsx first
    main_jsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);"""
    
    await _async_sandbox_file_write(sandbox, "my-app/src/main.jsx", main_jsx)
    
    # Create index.css
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Inter', sans-serif;
}"""
    
    await _async_sandbox_file_write(sandbox, "my-app/src/index.css", index_css)
    
    # Create a better fallback App
    fallback_app = """import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-2xl w-full mx-4">
        <div className="text-center">
          <div className="mb-6">
            <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mx-auto flex items-center justify-center">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            🚨 FALLBACK MODE ACTIVATED
          </h1>
          <p className="text-gray-600 mb-6">
            The AI-generated script failed to execute properly. This is a fallback React application.
            Please check the logs for script execution errors.
          </p>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-yellow-800 mb-2">Debug Information:</h3>
            <p className="text-sm text-yellow-700">
              • Script execution failed<br/>
              • Fallback app created<br/>
              • Check console logs for details
            </p>
          </div>
          <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
            Retry Generation
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;"""
    
    await _async_sandbox_file_write(sandbox, "my-app/src/App.jsx", fallback_app)
    print("✅ Enhanced fallback React app created with debug information")


async def _validate_react_components(sandbox) -> None:
    """Validate and fix React components."""
    try:
        print("🔍 Validating React components...")
        
        try:
            app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")
            print(f"📄 App.jsx content preview: {app_content[:200]}...")
            
            issues = []
            if "import React" not in app_content and "React" in app_content:
                issues.append("Missing React import")
            if "export default" not in app_content:
                issues.append("Missing export default")
            if "function " not in app_content and "const " not in app_content:
                issues.append("No component function found")
                
            if issues:
                print(f"⚠️ React issues found: {issues}")
                await _create_fallback_react_app(sandbox)
            else:
                print("✅ React component validation passed")
                
        except Exception as e:
            print(f"❌ App.jsx not found or invalid: {e}")
            await _create_fallback_react_app(sandbox)
            
    except Exception as e:
        print(f"⚠️ Component validation failed: {e}")


## **Enhanced Session Management**


# ```python:backend/nodes/apply_to_Sandbox_node.py
# Replace the entire function with:
def _kill_sandbox_for_session(session_id: str):
    """Kill sandbox for a specific session."""
    with _sandbox_lock:
        if session_id in _session_sandboxes:
            sandbox_info = _session_sandboxes[session_id]
            sandbox = sandbox_info.get("sandbox")
            if sandbox:
                try:
                    print(f"🔥 Killing sandbox for session: {session_id}")
                    sandbox.kill()
                    print(f"✅ Sandbox terminated for session: {session_id}")
                except Exception as e:
                    print(f"⚠️ Error terminating sandbox for session {session_id}: {e}")
            del _session_sandboxes[session_id]

# Replace the entire function with:
# at top of file:
import asyncio, time

# keep your existing: _sandbox_lock = threading.Lock()
# keep your existing _session_sandboxes dict

async def _get_or_create_persistent_sandbox(ctx: Dict[str, Any], sandbox_timeout: int):
    """Get or create sandbox for this session WITHOUT awaiting inside the global lock."""
    session_id = ctx.get("session_id", "default")

    # ---- QUICK LOOKUP (no await) ----
    with _sandbox_lock:
        entry = _session_sandboxes.get(session_id)
        sandbox = entry.get("sandbox") if entry else None

    # ---- HEALTH CHECK OUTSIDE LOCK ----
    if sandbox:
        try:
            ping = await _async_sandbox_command(sandbox, "echo ok", 5)
            proj = await _async_sandbox_command(sandbox, "ls my-app/package.json", 5)
            if getattr(ping, "exit_code", 1) == 0 and getattr(proj, "exit_code", 1) == 0:
                ctx["existing_sandbox_id"] = getattr(sandbox, "id", "unknown")
                return sandbox, False
        except Exception:
            pass
        # unregister broken sandbox
        with _sandbox_lock:
            _session_sandboxes.pop(session_id, None)

    # ---- CREATE NEW OUTSIDE LOCK ----
    new_sandbox = await _create_sandbox_with_timeout(sandbox_timeout)
    info = {
        "id": getattr(new_sandbox, "id", "unknown"),
        "created_at": time.time(),
        "project_setup": False,
        "session_id": session_id,
    }

    # ---- REGISTER ATOMICALLY ----
    with _sandbox_lock:
        _session_sandboxes[session_id] = {"sandbox": new_sandbox, "info": info}

    ctx["existing_sandbox_id"] = info["id"]
    print(f"✅ Created fresh sandbox for session {session_id}: {info['id']}")
    return new_sandbox, True


# Replace the entire function with:
async def _is_project_setup(session_id: str) -> bool:
    """Check if project is set up for this session without awaiting under the lock."""
    # read pointers quickly under lock
    with _sandbox_lock:
        entry = _session_sandboxes.get(session_id)
        if not entry:
            return False
        sandbox = entry.get("sandbox")
        info = entry.get("info", {})
        if info.get("project_setup"):
            return True

    if not sandbox:
        return False

    # do checks outside lock
    try:
        dir_check = await _async_sandbox_command(sandbox, "ls -la", 10)
        if getattr(dir_check, "exit_code", 1) != 0:
            return False
        pkg = await _async_sandbox_file_read(sandbox, "my-app/package.json")
        if not pkg or "vite" not in pkg:
            return False
        nm = await _async_sandbox_command(sandbox, "ls -la my-app/", 10)
        if getattr(nm, "exit_code", 1) != 0 or "node_modules" not in nm.stdout:
            return False

        # mark setup true under lock
        with _sandbox_lock:
            if session_id in _session_sandboxes:
                _session_sandboxes[session_id]["info"]["project_setup"] = True
        return True
    except Exception as e:
        print(f"⚠️ Error checking project setup for session {session_id}: {e}")
        return False



async def _apply_file_corrections_only(correction_data: Dict[str, Any], session_id: str) -> bool:
    """Apply ONLY file corrections to the existing sandbox with robust validation."""
    sandbox = _get_session_sandbox(session_id)
    
    if not sandbox:
        print("❌ No persistent sandbox available for corrections")
        return False
    
    try:
        print("🔧 Applying file corrections to existing sandbox...")
        
        # STEP 1: VALIDATE PROJECT STRUCTURE BEFORE CORRECTIONS
        if not await _validate_project_structure(sandbox):
            print("❌ Project structure invalid before corrections - cannot proceed")
            return False
        
        # STEP 2: BACKUP CRITICAL FILES
        backup_files = await _backup_critical_files(sandbox)
        if not backup_files:
            print("⚠️ Could not backup critical files, proceeding with caution")
        
        # STEP 3: APPLY CORRECTIONS WITH VALIDATION
        files_to_correct = correction_data.get("files_to_correct", [])
        for file_correction in files_to_correct:
            file_path = file_correction.get("path", "")
            corrected_content = file_correction.get("corrected_content", "")
            
            if file_path and corrected_content:
                print(f"   📝 Correcting file: {file_path}")
                
                # Ensure proper file path
                full_path = f"my-app/{file_path}" if not file_path.startswith("my-app/") else file_path
                
                try:
                    # Validate content before writing
                    if not await _validate_file_content(file_path, corrected_content):
                        print(f"   ⚠️ Content validation failed for {file_path}, skipping")
                        continue
                    
                    await _async_sandbox_file_write(sandbox, full_path, corrected_content)
                    print(f"   ✅ Updated: {file_path}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to update {file_path}: {e}")
                    # Restore from backup if available
                    if backup_files and file_path in backup_files:
                        await _async_sandbox_file_write(sandbox, full_path, backup_files[file_path])
                        print(f"   🔄 Restored {file_path} from backup")
                    return False
        
        # STEP 4: CREATE NEW FILES
        new_files = correction_data.get("new_files", [])
        for file_info in new_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")
            
            if file_path and content:
                print(f"   📄 Creating new file: {file_path}")
                full_path = f"my-app/{file_path}" if not file_path.startswith("my-app/") else file_path
                
                try:
                    await _async_sandbox_file_write(sandbox, full_path, content)
                    print(f"   ✅ Created: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to create {file_path}: {e}")
                    return False
        
        # STEP 5: VALIDATE PROJECT STRUCTURE AFTER CORRECTIONS
        if not await _validate_project_structure(sandbox):
            print("❌ Project structure corrupted after corrections - restoring from backup")
            if backup_files:
                await _restore_from_backup(sandbox, backup_files)
                print("🔄 Project restored from backup")
                return False
            else:
                print("❌ No backup available - project corrupted")
                return False
        
        # STEP 6: VALIDATE CRITICAL FILES
        if not await _validate_critical_files(sandbox):
            print("❌ Critical files corrupted after corrections")
            return False
        
        print("✅ All file corrections applied successfully with validation")
        return True
        
    except Exception as e:
        print(f"❌ Error applying file corrections: {e}")
        # Restore from backup if available
        if 'backup_files' in locals() and backup_files:
            await _restore_from_backup(sandbox, backup_files)
            print("🔄 Project restored from backup after error")
        return False


async def _restart_dev_server_only(session_id: str) -> Optional[str]:
    """Restart ONLY the dev server in the persistent sandbox, robustly."""
    sandbox = _get_session_sandbox(session_id)
    
    # Add port definition
    port = int(os.getenv("E2B_VITE_PORT", "5173"))
    
    if not sandbox:
        print("❌ No persistent sandbox available for dev server restart")
        return None
    
    print("🔄 Restarting dev server in existing sandbox...")
    try:
        # STEP 1: Validate project structure before restart
        if not await _validate_project_structure(sandbox):
            print("   ❌ Project structure invalid - cannot restart")
            return None
        
        # STEP 2: Validate corrected files
        print("   🔍 Validating corrected files before restart...")
        try:
            app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")
            if not app_content or "function " not in app_content:
                print("   ⚠️ Invalid App.jsx, creating fallback")
                await _create_fallback_react_app(sandbox)
        except Exception:
            print("   ⚠️ Error reading App.jsx, creating fallback")
            await _create_fallback_react_app(sandbox)

        # STEP 3: Stop existing servers
        print("   🛑 Stopping existing dev server...")
        await _async_sandbox_command(sandbox, "bash -lc \"pkill -f 'npm run dev' || true\"", 10)
        await _async_sandbox_command(sandbox, "bash -lc \"pkill -f 'vite' || true\"", 10)

        import time as _t
        await asyncio.sleep(2)

        # STEP 4: Clear caches
        await _async_sandbox_command(sandbox, "bash -lc \"cd my-app && rm -rf .vite node_modules/.vite dev.log || true\"", 10)

        # STEP 5: Start dev server
        print("   🚀 Starting dev server...")
        await _async_sandbox_command(sandbox,
            f"bash -lc \"cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &\"",
            timeout=30,
        )

        # STEP 6: Wait for server with reduced attempts
        if not await _wait_for_http(sandbox, port, max_attempts=5):
            print("   ⚠️ Dev server did not become ready after restart")
            return None

        host = sandbox.get_host(port)
        url = f"https://{host}"
        print(f"   ✅ Dev server restarted at: {url}")
        return url

    except Exception as e:
        print(f"❌ Error restarting dev server: {e}")
        return None

async def _install_package(sandbox: Sandbox, package_name: str) -> bool:
    """Install a single package with enhanced verification"""
    print(f"📦 Installing {package_name}...")
    try:
        # Run installation in the project directory
        command = f"cd my-app && npm install {package_name} --save"
        result = await _async_sandbox_command(sandbox, command, 300)
        
        # Check installation success by exit code
        if result.exit_code != 0:
            print(f"   ❌ Installation failed with exit code {result.exit_code}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
        
        # Verify installation by checking package.json or node_modules
        verify_command = f"cd my-app && npm list {package_name} --depth=0"
        verify_result = await _async_sandbox_command(sandbox, verify_command, 30)
        
        # FIX: Check the stdout property, not the object directly
        if verify_result and verify_result.stdout and package_name in verify_result.stdout:
            print(f"   ✅ Verified {package_name} installation")
            return True
        else:
            print(f"   ❌ Installation verification failed for {package_name}")
            if verify_result and verify_result.stdout:
                print(f"   npm list output: {verify_result.stdout}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error installing {package_name}: {e}")
        return False

async def _detect_and_install_dependencies(sandbox: Sandbox, script_content: str) -> List[str]:
    print("🔍 Analyzing generated React code for dependencies...")
    
    # WHITELIST of allowed packages - ONLY these will be installed
    ALLOWED_PACKAGES = {
        'react-dom', 'lucide-react', 'react-icons', '@heroicons/react',
        'framer-motion', '@radix-ui/react-dialog', '@radix-ui/react-slot',
        'class-variance-authority', 'clsx', 'tailwind-merge', 'react-router-dom', 'react-router'
        # Expanded list to include common UI libraries
    }
    
    potential_packages = set()
    
    # FIXED: More specific regex to avoid matching random text or numbers.
    # This now looks for standard import/from patterns.
    patterns = [
        r'import\s+.*?from\s+["\']([^"\'.\s/][^"\']*)["\']',  # `import {..} from 'package'`
        r'import\s+["\']([^"\'.\s/][^"\']*)["\']',            # `import 'package'`
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, script_content)
        for match in matches:
            # Filter out relative paths and built-ins
            if not match.startswith('.') and not match.startswith('/'):
                package_name = match  # Use the full string from the import
                if package_name in ALLOWED_PACKAGES:
                    potential_packages.add(package_name)
                else:
                    # Also check for root package of scoped packages (e.g., @heroicons/react from @heroicons/react/24/solid)
                    if '/' in package_name:
                        root_package = '/'.join(package_name.split('/')[:2])
                        if root_package in ALLOWED_PACKAGES:
                            potential_packages.add(root_package)
                        else:
                            print(f"⚠️ Skipping blocked package: {package_name} (not in whitelist)")
                    else:
                        print(f"⚠️ Skipping blocked package: {package_name} (not in whitelist)")

    
    # Filter out built-in modules
    builtin_packages = {'path', 'fs', 'os', 'child_process', 'react'}
    packages_to_install = [pkg for pkg in potential_packages if pkg not in builtin_packages]
    
    print(f"📦 Found {len(packages_to_install)} packages to install: {', '.join(packages_to_install)}")
    
    # Install packages
    installed = []
    for package in packages_to_install:
        if await _install_package(sandbox, package):
            installed.append(package)
    
    return installed


def _extract_code_files_from_script(script: str) -> Dict[str, str]:
    """
    Extract all the file writes from the generated script to analyze imports.
    """
    files = {}
    
    # Pattern to match sandbox.files.write calls
    file_write_pattern = r'sandbox\.files\.write\(["\']([^"\']+)["\'],\s*([^)]+)\)'
    matches = re.findall(file_write_pattern, script, re.DOTALL)
    
    for file_path, content_var in matches:
        # Try to find the content variable definition
        content_pattern = rf'{re.escape(content_var)}\s*=\s*["\'\`]([^"\'\`]*)["\'\`]'
        content_match = re.search(content_pattern, script, re.DOTALL)
        if content_match:
            files[file_path] = content_match.group(1)
    
    return files


async def _ensure_tailwind_build(sandbox) -> bool:
    """
    Ensure Tailwind CSS is properly built and ready.
    """
    print("🎨 Ensuring Tailwind CSS is properly built...")
    
    try:
        # Check if Tailwind config exists and is properly set up
        try:
            tailwind_config = await _async_sandbox_file_read(sandbox, "my-app/tailwind.config.js")
            if "content:" not in tailwind_config:
                print("⚠️ Tailwind config missing content paths, fixing...")
                fixed_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
                await _async_sandbox_file_write(sandbox, "my-app/tailwind.config.js", fixed_config)
                print("✅ Fixed Tailwind config")
        except:
            print("⚠️ Tailwind config not found, creating...")
            config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""
            await _async_sandbox_file_write(sandbox, "my-app/tailwind.config.js", config)
            print("✅ Created Tailwind config")
        
        # Ensure PostCSS config exists
        try:
            await _async_sandbox_file_read(sandbox, "my-app/postcss.config.js")
        except:
            print("⚠️ PostCSS config not found, creating...")
            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
            await _async_sandbox_file_write(sandbox, "my-app/postcss.config.js", postcss_config)
            print("✅ Created PostCSS config")
        
        # Force rebuild CSS by clearing Vite cache and rebuilding
        print("🔄 Clearing Vite cache and rebuilding...")
        await _async_sandbox_command(sandbox, "cd my-app && rm -rf node_modules/.vite", 10)
        await _async_sandbox_command(sandbox, "cd my-app && rm -rf .vite", 10)
        
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring Tailwind build: {e}")
        return False


async def _verify_css_content(sandbox: Sandbox) -> bool:
    """Verify CSS content is properly set up"""
    print("🔍 Verifying CSS content...")
    try:
        # 1. Check index.css contains Tailwind directives
        css_content = await _async_sandbox_file_read(sandbox, "my-app/src/index.css")
        if "@tailwind base" not in css_content:
            print("❌ Tailwind base directive missing in index.css")
            return False
        if "@tailwind components" not in css_content:
            print("❌ Tailwind components directive missing in index.css")
            return False
        if "@tailwind utilities" not in css_content:
            print("❌ Tailwind utilities directive missing in index.css")
            return False
            
        # 2. Check main.jsx imports index.css
        main_content = await _async_sandbox_file_read(sandbox, "my-app/src/main.jsx")
        if "import './index.css'" not in main_content:
            print("❌ index.css import missing in main.jsx")
            return False
            
        print("✅ CSS content verified")
        return True
    except Exception as e:
        print(f"⚠️ CSS content verification failed: {e}")
        return False


# Main function
import time

async def apply_sandbox(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply Sandbox Node with SESSION-BASED sandbox management and robust EDIT support."""
    print("--- Running Apply Sandbox Node (Enhanced with Edit Support) ---")

    ctx = state.get("context", {}) or {}
    # gen_result = ctx.get("generation_result", {}) or {}
    # script_to_run = gen_result.get("e2b_script")
    # is_correction = gen_result.get("is_correction", False)
    # is_edit = gen_result.get("is_edit", False)

    session_id = state.get("session_id") or state.get("metadata", {}).get("session_id", "default")
    ctx["session_id"] = session_id
    state["context"] = ctx
    # port = int(os.getenv("E2B_VITE_PORT", "5173"))
    # sandbox_timeout = int(os.getenv("E2B_SANDBOX_TIMEOUT", "3600"))

    # ---------------------------------------------------------------------
    # 1️⃣ EDIT MODE HANDLING (PATCHES EXISTING APP)
    # ---------------------------------------------------------------------
    lock = _session_exec_locks[session_id]
    async with lock:
        gen_result = ctx.get("generation_result", {}) or {}
        script_to_run = gen_result.get("e2b_script")
        is_correction = gen_result.get("is_correction", False)
        is_edit = gen_result.get("is_edit", False)
        port = int(os.getenv("E2B_VITE_PORT", "5173"))
        sandbox_timeout = int(os.getenv("E2B_SANDBOX_TIMEOUT", "3600"))
        if is_edit:
            print("🔄 EDIT MODE - Applying targeted changes to existing application...")
            sandbox = await _get_existing_sandbox_only(ctx)
            if not sandbox:
                msg = "No existing sandbox found during edit - cannot apply changes"
                print(f"❌ {msg}")
                return {"error": msg}

            correction_data = ctx.get("correction_data", {})
            if not correction_data:
                msg = "No correction data found for edit mode"
                print(f"❌ {msg}")
                return {"error": msg}

            if not await _apply_edit_changes(correction_data, session_id):
                raise RuntimeError("Failed to apply edit changes")

            # Restart dev server (or full start if needed)
            final_url = await _restart_dev_server_only(session_id)
            if not final_url:
                print("⚠️ Restart failed, trying full start...")
                public_host = sandbox.get_host(port)
                await _write_vite_config(sandbox, public_host, port)
                try:
    # ⏱️ 3-minute hard limit for dev-server + preview start
                    async with asyncio.timeout(180):
                        final_url = await _start_dev_server(sandbox, port=port)
                        if not final_url:
                            final_url = await _start_preview_server(sandbox, port_primary=port, port_fallback=4173)
                except TimeoutError:
                    print(f"⏱️ Dev server start timed out for session {session_id}")
                    _kill_sandbox_for_session(session_id)
                    ctx["sandbox_failed"] = True
                    ctx["sandbox_error"] = "Timeout waiting for dev server"
                    state["context"] = ctx
                    return state

                if not final_url:
                    print(f"❌ Failed to start dev server for session {session_id}")
                    _kill_sandbox_for_session(session_id)
                    ctx["sandbox_failed"] = True
                    ctx["sandbox_error"] = "Dev server failed"
                    state["context"] = ctx
                    return state


            # Store full app state after edits
            sandbox_id = getattr(sandbox, "id", "unknown")
            complete_state =await _capture_complete_application_state(sandbox)
            if complete_state:
                ctx["generation_result"] = complete_state
                print("✅ Captured complete application state after edit")

            ctx["sandbox_result"] = {
                "success": True,
                "url": final_url,
                "port": port,
                "sandbox_id": sandbox_id,
                "message": "Edit changes applied successfully and server restarted"
            }
            state["context"] = ctx
            return state

        # ---------------------------------------------------------------------
        # 2️⃣ CORRECTION MODE (REUSES SANDBOX, RESTARTS SERVER)
        # ---------------------------------------------------------------------
        if is_correction:
            print("🔄 CORRECTION MODE - Restarting Vite server with corrections...")
            sandbox = await _get_existing_sandbox_only(ctx)
            if not sandbox:
                return {"error": "Correction failed - no existing sandbox found"}
            try:
                restart_result = await _restart_dev_server_only(session_id)
                if restart_result:
                    print("✅ Vite server restarted successfully with corrections")
                    return {"success": True, "message": "Corrections applied and server restarted"}
                else:
                    print("❌ Failed to restart server, attempting full start...")
                    public_host = sandbox.get_host(port)
                    await _write_vite_config(sandbox, public_host, port)
                    final_url = await _start_dev_server(sandbox, port=port)
                    if not final_url:
                        final_url = await _start_preview_server(sandbox, port_primary=port, port_fallback=4173)
                    return {"success": bool(final_url), "url": final_url}
            except Exception as e:
                print(f"❌ Error restarting Vite server: {e}")
                return {"error": str(e)}

        # ---------------------------------------------------------------------
        # 3️⃣ INITIAL GENERATION (FULL APP CREATION)
        # ---------------------------------------------------------------------
        if not script_to_run:
            msg = "No script to run in generation result"
            print(f"❌ {msg}")
            return {"error": msg}

        if not os.getenv("E2B_API_KEY"):
            msg = "E2B_API_KEY is not set; please configure your environment."
            print(f"❌ {msg}")
            ctx["sandbox_result"] = {"success": False, "error": msg}
            state["context"] = ctx
            return state

        try:
            sandbox, newly_created = await _get_or_create_persistent_sandbox(ctx, sandbox_timeout)
            print(f"✅ Using sandbox: {getattr(sandbox, 'id', 'unknown')} (newly_created={newly_created})")

            # Ensure project setup
            if not await _is_project_setup(session_id):
                print("📦 Setting up base Vite project...")
                if not await _create_fast_vite_project(sandbox):
                    raise RuntimeError("Failed to create base Vite project")
                with _sandbox_lock:
                    if session_id in _session_sandboxes:
                        _session_sandboxes[session_id]["info"]["project_setup"] = True
            else:
                print("✅ Project already set up")

            # Dependency installation
            normalized = _normalize_e2b_api(script_to_run)
            print("🔍 Analyzing script for dependencies...")
            try:
                installed_packages = await _detect_and_install_dependencies(sandbox, normalized)
                if installed_packages:
                    print(f"✅ Installed packages: {', '.join(installed_packages)}")
                    await asyncio.sleep(2)  # let npm settle
                else:
                    print("✅ No additional packages required")
            except Exception as dep_error:
                print(f"⚠️ Dependency detection failed: {dep_error}")

            # Execute generator script
            script_execution_success = False
            try:
                ns: Dict[str, Any] = {"Sandbox": Sandbox, "sandbox": sandbox}
                exec(normalized, ns)
                print(f"🔍 Namespace keys: {list(ns.keys())}")

                main_function = None
                for key in ns:
                    if key.startswith("create_") and key.endswith("_app") and callable(ns[key]):
                        main_function = ns[key]
                        print(f"✅ Found main generator function: {key}")
                        break

                if main_function:
                    result = main_function(sandbox)
                    print(f"✅ Script executed successfully: {result}")
                    script_execution_success = True
                else:
                    print("❌ No generator function found in script output")

            except Exception as e:
                import traceback
                print(f"❌ Script execution failed: {e}")
                print(traceback.format_exc())

            if not script_execution_success:
                print("🔧 Falling back to creating a fresh React app...")
                await _create_fallback_react_app(sandbox)
                print("✅ Fallback React app created successfully")

            # Ensure CSS setup
            await _ensure_css_files(sandbox)
            await _fix_vite_css_processing(sandbox)
            await _ensure_tailwind_cdn_in_index_html(sandbox)

            # Clear vite cache before starting server
            await _async_sandbox_command(sandbox, "cd my-app && rm -rf node_modules/.vite", 10)
            await _async_sandbox_command(sandbox, "cd my-app && rm -rf .vite", 10)

            # Start dev server (or fallback to preview)
            public_host = sandbox.get_host(port)
            await _write_vite_config(sandbox, public_host, port)
            final_url = await _start_dev_server(sandbox, port=port)
            if not final_url:
                final_url = await _start_preview_server(sandbox, port_primary=port, port_fallback=4173)

            if not final_url:
                raise RuntimeError("Dev server not accessible after generation")

            ctx["sandbox_result"] = {
                "success": True,
                "url": final_url,
                "port": port,
                "sandbox_id": getattr(sandbox, "id", "unknown"),
                "message": "Application deployed successfully"
            }

        except Exception as e:
            import traceback
            print(f"❌ Sandbox application failed: {e}")
            print(traceback.format_exc())
            
            # 🔥 ADD THIS LINE
            _kill_sandbox_for_session(session_id)

            ctx["sandbox_result"] = {"success": False, "error": str(e)}
            ctx["sandbox_failed"] = True
            ctx["sandbox_error"] = str(e)
            state["context"] = ctx
            return state

    state["context"] = ctx
    return state



async def _capture_complete_application_state(sandbox) -> Dict[str, Any]:
    """Capture the complete application state after successful edit for proper storage."""
    print("📁 Capturing complete application state after edit...")
    
    try:
        complete_state = {
            "e2b_script": None,  # Will be generated
            "is_correction": False,
            "is_edit": False,
            "complete_files": {}
        }
        
        # Capture all application files
        critical_files = [
            "src/App.jsx", "src/main.jsx", "src/index.css", "package.json", "index.html"
        ]
        
        # Also capture any component files
        try:
            # List all files in src directory
            src_files_result = await _async_sandbox_command(sandbox, "find my-app/src -name '*.jsx' -o -name '*.js' -o -name '*.css'", 10)
            if src_files_result and src_files_result.stdout:
                additional_files = [f.strip() for f in src_files_result.stdout.split('\n') if f.strip()]
                for file_path in additional_files:
                    if file_path not in critical_files:
                        critical_files.append(file_path.replace('my-app/', ''))
        except Exception as e:
            print(f"⚠️ Could not list additional files: {e}")
        
        # Read all files
        for file_path in critical_files:
            try:
                full_path = f"my-app/{file_path}"
                content = await _async_sandbox_file_read(sandbox, full_path)
                if content:
                    complete_state["complete_files"][file_path] = content
                    print(f"   ✅ Captured: {file_path}")
            except Exception as e:
                print(f"   ⚠️ Could not capture {file_path}: {e}")
        
        # Generate a proper e2b_script that recreates the complete application
        script_lines = []
        script_lines.append("def create_react_app(sandbox):")
        script_lines.append('    """Recreate complete application from stored state"""')
        script_lines.append("    print('Recreating complete application from stored state...')")
        
        for file_path, content in complete_state["complete_files"].items():
            # Properly escape the content for Python
            escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            script_lines.append(f'    # Recreate {file_path}')
            script_lines.append(f'    {file_path.replace("/", "_").replace(".", "_")}_content = """{escaped_content}"""')
            script_lines.append(f'    sandbox.files.write("my-app/{file_path}", {file_path.replace("/", "_").replace(".", "_")}_content)')
            script_lines.append(f'    print(f"✅ Recreated {file_path}")')
        
        script_lines.append("    print('✅ Complete application recreated successfully')")
        script_lines.append("    return 'Complete application recreated from stored state'")
        
        # Create the complete script
        complete_script = "\n".join(script_lines)
        complete_state["e2b_script"] = complete_script
        
        print(f"✅ Captured complete application state with {len(complete_state['complete_files'])} files")
        return complete_state
        
    except Exception as e:
        print(f"❌ Error capturing complete application state: {e}")
        return None

def _fix_tailwind_postcss_plugin(sandbox: Sandbox) -> bool:
    """No longer needed - Tailwind comes from CDN"""
    print("✅ Tailwind CSS is loaded via CDN - no PostCSS setup needed")
    return True

async def _try_alternative_postcss_setup(sandbox: Sandbox) -> bool:
    """Try alternative PostCSS setup if the main one fails"""
    print("🔄 TRYING ALTERNATIVE POSTCSS SETUP...")
    
    try:
        # Method 1: Use the fallback config
        print("📝 Switching to fallback PostCSS config...")
        await _async_sandbox_command(sandbox, "cd my-app && mv postcss.config.fallback.js postcss.config.js", 5)
        
        # Method 2: If that doesn't work, try CommonJS format
        print("📝 Creating CommonJS PostCSS config...")
        commonjs_postcss = """module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        await _async_sandbox_file_write(sandbox, "my-app/postcss.config.cjs", commonjs_postcss)
        
        # Method 3: Try without the separate plugin
        print("📝 Creating simple PostCSS config...")
        simple_postcss = """export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        await _async_sandbox_file_write(sandbox, "my-app/postcss.config.simple.js", simple_postcss)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in alternative PostCSS setup: {e}")
        return False


async def _fix_vite_css_processing(sandbox: Sandbox) -> bool:
    """Minimal Vite config - no PostCSS needed"""
    print("🔧 FIXING VITE CSS PROCESSING...")
    
    try:
        # Minimal Vite config; CSS is handled by CDN
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    hmr: false
  },
  preview: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  }
})"""
        
        await _async_sandbox_file_write(sandbox, "my-app/vite.config.js", vite_config)
        print("✅ Updated Vite config for CDN-based Tailwind")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Vite CSS processing: {e}")
        return False

async def _validate_project_structure(sandbox: Sandbox) -> bool:
    """Validate that the project structure is intact."""
    print("🔍 Validating project structure...")
    
    critical_files = [
        "my-app/package.json",
        "my-app/src/main.jsx", 
        "my-app/src/App.jsx",
        "my-app/src/index.css"
    ]
    
    for file_path in critical_files:
        try:
            content = await _async_sandbox_file_read(sandbox, file_path)
            if not content:
                print(f"❌ Critical file empty: {file_path}")
                return False
        except Exception as e:
            print(f"❌ Critical file missing: {file_path} - {e}")
            return False
    
    # Check if npm commands work
    try:
        result = await _async_sandbox_command(sandbox, "cd my-app && npm --version", 10)
        if result.exit_code != 0:
            print("❌ npm not working in project directory")
            return False
    except Exception as e:
        print(f"❌ Cannot verify npm: {e}")
        return False
    
    print("✅ Project structure validation passed")
    return True

async def _validate_critical_files(sandbox: Sandbox) -> bool:
    """Validate that critical files contain valid content."""
    print("🔍 Validating critical file contents...")
    
    try:
        # Check App.jsx has valid React component
        app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")
        if not app_content or "function " not in app_content or "export default" not in app_content:
            print("❌ App.jsx is not a valid React component")
            return False
        
        # Check main.jsx has proper imports
        main_content = await _async_sandbox_file_read(sandbox, "my-app/src/main.jsx")
        if not main_content or "import App" not in main_content:
            print("❌ main.jsx missing App import")
            return False
        
        # Check package.json has required fields
        package_content = await _async_sandbox_file_read(sandbox, "my-app/package.json")
        if not package_content or "dependencies" not in package_content:
            print("❌ package.json missing dependencies")
            return False
        
        print("✅ Critical file validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating critical files: {e}")
        return False

async def _backup_critical_files(sandbox: Sandbox) -> Dict[str, str]:
    """Backup critical files before making corrections."""
    print("🔄 Creating backup of critical files...")
    
    backup_files = {}
    critical_files = [
        "my-app/src/App.jsx",
        "my-app/src/main.jsx",
        "my-app/src/index.css",
        "my-app/package.json"
    ]
    
    for file_path in critical_files:
        try:
            content = await _async_sandbox_file_read(sandbox, file_path)
            if content:
                backup_files[file_path] = content
                print(f"   ✅ Backed up: {file_path}")
        except Exception as e:
            print(f"   ⚠️ Could not backup {file_path}: {e}")
    
    print(f"🔄 Backup created for {len(backup_files)} files")
    return backup_files

async def _restore_from_backup(sandbox: Sandbox, backup_files: Dict[str, str]) -> bool:
    """Restore project from backup files."""
    print("🔄 Restoring project from backup...")
    
    try:
        for file_path, content in backup_files.items():
            try:
                await _async_sandbox_file_write(sandbox, file_path, content)
                print(f"   ✅ Restored: {file_path}")
            except Exception as e:
                print(f"   ❌ Failed to restore {file_path}: {e}")
                return False
        
        print("✅ Project restored from backup successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring from backup: {e}")
        return False

async def _validate_file_content(file_path: str, content: str) -> bool:
    """Validate file content before writing."""
    
    # Basic content validation
    if not content or len(content.strip()) < 10:
        print(f"   ⚠️ Content too short for {file_path}")
        return False
    
    # File-specific validation
    if file_path.endswith('.jsx') or file_path.endswith('.js'):
        if "import React" not in content and "React" in content:
            print(f"   ⚠️ {file_path} missing React import")
            return False
        
        if "export default" not in content and "function " in content:
            print(f"   ⚠️ {file_path} missing export default")
            return False
    
    elif file_path.endswith('.css'):
        if "@tailwind" not in content:
            print(f"   ⚠️ {file_path} missing Tailwind directives")
            return False
    
    return True

async def _get_existing_sandbox_only(ctx: Dict[str, Any]):
    """Get existing sandbox ONLY - never create new one during corrections."""
    session_id = ctx.get("session_id", "default")
    sandbox = _get_session_sandbox(session_id)
    
    if sandbox is None:
        return None
    
    try:
        # Quick health check
        test_result = await _async_sandbox_command(sandbox, "echo 'test'", 5)
        if test_result and test_result.stdout:
            sandbox_id = getattr(sandbox, "id", "unknown")
            print(f"✅ Found existing sandbox: {sandbox_id}")
            return sandbox
    except Exception as e:
        print(f"⚠️ Sandbox health check failed: {e}")
    
    return None

async def _apply_edit_changes(correction_data: Dict[str, Any], session_id: str) -> bool:
    """Apply edit changes to the existing sandbox with robust validation and dependency installation."""
    sandbox = _get_session_sandbox(session_id)
    
    if not sandbox:
        print("❌ No persistent sandbox available for edits")
        return False
    
    try:
        print("🔧 Applying edit changes to existing sandbox...")
        
        # STEP 1: VALIDATE PROJECT STRUCTURE BEFORE EDITS
        if not await _validate_project_structure(sandbox):
            print("❌ Project structure invalid before edits - cannot proceed")
            return False
        
        # STEP 2: BACKUP CRITICAL FILES
        backup_files = await _backup_critical_files(sandbox)
        if not backup_files:
            print("⚠️ Could not backup critical files, proceeding with caution")
        
        # STEP 3: COLLECT ALL FILE CONTENTS FOR DEPENDENCY ANALYSIS
        all_new_content = []
        files_to_correct = correction_data.get("files_to_correct", [])
        new_files = correction_data.get("new_files", [])
        
        # Collect content from files being corrected
        for file_correction in files_to_correct:
            content = file_correction.get("corrected_content", "")
            if content:
                all_new_content.append(content)
        
        # Collect content from new files
        for file_info in new_files:
            content = file_info.get("content", "")
            if content:
                all_new_content.append(content)
        
        # STEP 4: DETECT AND INSTALL NEW DEPENDENCIES
        if all_new_content:
            print("🔍 Analyzing edited/new files for dependencies...")
            combined_content = "\n".join(all_new_content)
            
            try:
                installed_packages = await _detect_and_install_dependencies(sandbox, combined_content)
                if installed_packages:
                    print(f"✅ Successfully installed {len(installed_packages)} new packages: {', '.join(installed_packages)}")
                    # Give npm a moment to update package.json and node_modules
                    await asyncio.sleep(2)
                else:
                    print("ℹ️ No new dependencies detected in edited files")
            except Exception as e:
                print(f"⚠️ Warning: Could not install dependencies: {e}")
                # Continue with edits even if dependency installation fails
        
        # STEP 5: APPLY EDITS WITH VALIDATION
        print(f"📝 Applying edits to {len(files_to_correct)} files...")
        
        for file_correction in files_to_correct:
            file_path = file_correction.get("path", "")
            corrected_content = file_correction.get("corrected_content", "")
            
            if file_path and corrected_content:
                print(f"   📝 Editing file: {file_path}")
                
                # Ensure proper file path
                full_path = f"my-app/{file_path}" if not file_path.startswith("my-app/") else file_path
                
                try:
                    # Validate content before writing
                    if not await _validate_file_content(file_path, corrected_content):
                        print(f"   ⚠️ Content validation failed for {file_path}, skipping")
                        continue
                    
                    # CRITICAL: Write the modified content
                    await _async_sandbox_file_write(sandbox, full_path, corrected_content)
                    print(f"   ✅ Updated: {file_path}")
                    
                    # Verify the change was applied
                    verify_content = await _async_sandbox_file_read(sandbox, full_path)
                    if verify_content == corrected_content:
                        print(f"   ✅ Verified: {file_path} updated successfully")
                    else:
                        print(f"   ⚠️ Warning: {file_path} content may not have updated correctly")
                    
                except Exception as e:
                    print(f"   ❌ Failed to update {file_path}: {e}")
                    # Restore from backup if available
                    if backup_files and file_path in backup_files:
                        await _async_sandbox_file_write(sandbox, full_path, backup_files[file_path])
                        print(f"   🔄 Restored {file_path} from backup")
                    return False
        
        # STEP 6: CREATE NEW FILES (if any)
        for file_info in new_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")
            
            if file_path and content:
                print(f"   📄 Creating new file: {file_path}")
                full_path = f"my-app/{file_path}" if not file_path.startswith("my-app/") else file_path
                
                try:
                    await _async_sandbox_file_write(sandbox, full_path, content)
                    print(f"   ✅ Created: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to create {file_path}: {e}")
                    return False
        
        # STEP 7: VALIDATE PROJECT STRUCTURE AFTER EDITS
        if not await _validate_project_structure(sandbox):
            print("❌ Project structure corrupted after edits - restoring from backup")
            if backup_files:
                await _restore_from_backup(sandbox, backup_files)
                print("🔄 Project restored from backup")
                return False
            else:
                print("❌ No backup available - project corrupted")
                return False
        
        # STEP 8: VALIDATE CRITICAL FILES
        if not await _validate_critical_files(sandbox):
            print("❌ Critical files corrupted after edits")
            return False
        
        print("✅ All edit changes applied successfully with validation")
        return True
        
    except Exception as e:
        print(f"❌ Error applying edit changes: {e}")
        # Restore from backup if available
        if 'backup_files' in locals() and backup_files:
            await _restore_from_backup(sandbox, backup_files)
            print("🔄 Project restored from backup after error")
        return False

def cleanup_session_sandbox(session_id: str):
    """Clean up sandbox for a specific session"""
    with _sandbox_lock:
        if session_id in _session_sandboxes:
            sandbox = _session_sandboxes[session_id]["sandbox"]
            try:
                sandbox.kill()
                print(f"✅ Cleaned up sandbox for session: {session_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up sandbox for session {session_id}: {e}")
            del _session_sandboxes[session_id]

def cleanup_all_sessions():
    """Clean up all session sandboxes"""
    with _sandbox_lock:
        for session_id in list(_session_sandboxes.keys()):
            cleanup_session_sandbox(session_id)
