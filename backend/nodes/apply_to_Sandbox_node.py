import os
import re
import time
from typing import Dict, Any, Optional, List

# E2B v2.x SDK
from e2b_code_interpreter import Sandbox

# Global sandbox state - ENHANCED with session tracking
_global_sandbox = None
_global_sandbox_info = None
_current_session_id = None

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


def _create_fast_vite_project(sandbox) -> bool:
    """Create a Vite + React project with CDN Tailwind."""
    print("Creating Vite project with optimized approach...")

    try:
        # 1) Scaffold Vite React app
        sandbox.commands.run("npm create vite@latest my-app -- --template react", timeout=180)

        # 2) Install dependencies
        sandbox.commands.run("cd my-app && npm install", timeout=300)

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
        sandbox.files.write("my-app/index.html", index_html)

        print("✅ Vite project created with CDN Tailwind")
        return True

    except Exception as e:
        print(f"❌ Error creating Vite project: {e}")
        return False


def _ensure_css_files(sandbox: Sandbox):
    print("🎨 Ensuring comprehensive CSS files...")
    try:
        # Ensure index.css exists with Tailwind directives
        index_css_path = "my-app/src/index.css"
        
        # Always create a fresh index.css with proper content
        css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        sandbox.files.write(index_css_path, css_content)
        print("✅ Created fresh index.css with Tailwind directives")
            
        # Ensure main.jsx imports index.css
        main_jsx_path = "my-app/src/main.jsx"
        main_content = sandbox.files.read(main_jsx_path)
        if "import App from './App.jsx';" in main_content and "import './index.css'" not in main_content:
            main_content = main_content.replace(
                "import App from './App.jsx';",
                "import App from './App.jsx';\nimport './index.css';"
            )
            sandbox.files.write(main_jsx_path, main_content)
            print("✅ Added index.css import to main.jsx")
            
    except Exception as e:
        print(f"❌ Error ensuring CSS files: {e}")

def _ensure_tailwind_cdn_in_index_html(sandbox: Sandbox) -> bool:
    print("🎯 Ensuring Tailwind CDN in index.html...")
    try:
        path = "my-app/index.html"
        html = sandbox.files.read(path)
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
            
        sandbox.files.write(path, html)
        print("✅ Injected fresh Tailwind CDN into index.html")
        return True
    except Exception as e:
        print(f"❌ Failed to write index.html: {e}")
        return False



def _write_vite_config(sandbox, public_host: str, port: int) -> None:
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
        sandbox.files.write("my-app/vite.config.js", js_config)
        print("✅ Vite config patched with E2B host configuration.")
    except Exception as e:
        print(f"⚠️ Could not write vite config: {e}")


def _wait_for_http(sandbox, port: int, max_attempts: int = 5) -> bool:  # Reduced from 30 to 5
    """Wait for HTTP server to be ready - FIXED VERSION."""
    print(f"Checking if server is ready (attempt 1/{max_attempts})...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = sandbox.commands.run(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}", timeout=10)
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
            time.sleep(3)
    
    print(f"❌ Server not ready after {max_attempts} attempts")
    return False


def _start_dev_server(sandbox, port: int = 5173) -> Optional[str]:
    """Start the Vite dev server."""
    print("Starting development server (vite dev)...")

    try:
        sandbox.commands.run(
            f"bash -lc \"cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &\"",
            background=True,
        )

        if not _wait_for_http(sandbox, port):
            print("⚠️ Dev server did not become ready.")
            return None

        host = sandbox.get_host(port)
        url = f"https://{host}"
        print(f"✅ Dev server started at: {url}")
        return url

    except Exception as e:
        print(f"❌ Error starting dev server: {e}")
        return None


def _start_preview_server(sandbox, port_primary: int = 5173, port_fallback: int = 4173) -> Optional[str]:
    """Build and start Vite preview."""
    print("Starting preview server (vite preview) as fallback...")

    try:
        sandbox.commands.run("cd my-app && npm run build", timeout=480)

        sandbox.commands.run(
            f"bash -lc \"cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_primary} > preview.log 2>&1 &\"",
            background=True,
        )
        if _wait_for_http(sandbox, port_primary):
            host = sandbox.get_host(port_primary)
            return f"https://{host}"

        sandbox.commands.run(
            f"bash -lc \"cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_fallback} > preview_fallback.log 2>&1 &\"",
            background=True,
        )
        if _wait_for_http(sandbox, port_fallback):
            host = sandbox.get_host(port_fallback)
            return f"https://{host}"

        return None

    except Exception as e:
        print(f"❌ Error starting preview server: {e}")
        return None


def _create_sandbox_with_timeout(timeout_s: int):
    """Create a sandbox with timeout handling."""
    try:
        if hasattr(Sandbox, "create"):
            template_id = os.getenv("E2B_TEMPLATE_ID")
            if template_id:
                return Sandbox.create(template=template_id, timeout=timeout_s)
            return Sandbox.create(timeout=timeout_s)
        return Sandbox(timeout=timeout_s)
    except Exception as e:
        msg = str(e)
        if "Timeout cannot be greater than" in msg or "1 hours" in msg or "1 hour" in msg:
            print("⚠️ Provider rejected timeout. Retrying once with 3600s.")
            if hasattr(Sandbox, "create"):
                template_id = os.getenv("E2B_TEMPLATE_ID")
                if template_id:
                    return Sandbox.create(template=template_id, timeout=3600)
                return Sandbox.create(timeout=3600)
            return Sandbox(timeout=3600)
        raise


def _create_fallback_react_app(sandbox) -> None:
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
    
    sandbox.files.write("my-app/src/main.jsx", main_jsx)
    
    # Create index.css
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Inter', sans-serif;
}"""
    
    sandbox.files.write("my-app/src/index.css", index_css)
    
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
    
    sandbox.files.write("my-app/src/App.jsx", fallback_app)
    print("✅ Enhanced fallback React app created with debug information")


def _validate_react_components(sandbox) -> None:
    """Validate and fix React components."""
    try:
        print("🔍 Validating React components...")
        
        try:
            app_content = sandbox.files.read("my-app/src/App.jsx")
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
                _create_fallback_react_app(sandbox)
            else:
                print("✅ React component validation passed")
                
        except Exception as e:
            print(f"❌ App.jsx not found or invalid: {e}")
            _create_fallback_react_app(sandbox)
            
    except Exception as e:
        print(f"⚠️ Component validation failed: {e}")


## **Enhanced Session Management**


# ```python:backend/nodes/apply_to_Sandbox_node.py
def _kill_existing_sandbox():
    """Kill the existing sandbox to start fresh."""
    global _global_sandbox, _global_sandbox_info
    
    if _global_sandbox is not None:
        try:
            print("🔥 Killing existing sandbox to start fresh...")
            # Try to terminate the sandbox gracefully - FIX: use terminate() not close()
            _global_sandbox.kill()  # Changed from close() to kill()
            print("✅ Sandbox terminated successfully")
        except Exception as e:
            print(f"⚠️ Error terminating sandbox: {e}")
        finally:
            _global_sandbox = None
            _global_sandbox_info = None

def _get_or_create_persistent_sandbox(ctx: Dict[str, Any], sandbox_timeout: int):
    """Get or create sandbox with SMART management based on correction attempts."""
    global _global_sandbox, _global_sandbox_info, _current_session_id
    
    # Get current session ID with debug info
    current_session = ctx.get("session_id") or "default"
    
    # TRIGGER 1: New session detected
    if _current_session_id != current_session:
        print(f"🔄 New session detected: {current_session} (previous: {_current_session_id})")
        _kill_existing_sandbox()
        _current_session_id = current_session
    
    # TRIGGER 2: Check if we should create new sandbox based on correction attempts
    correction_attempts = ctx.get("correction_attempts", 0)
    total_attempts = ctx.get("total_attempts", 0)
    is_correction = ctx.get("is_correction", False)
    
    # FIX: Force new sandbox when switching to regenerate mode
    should_create_new_sandbox = False
    
    if correction_attempts >= 2:
        print(f"🔄 Correction attempts ({correction_attempts}) reached limit - FORCING NEW SANDBOX")
        should_create_new_sandbox = True
    elif total_attempts >= 5:
        print(f"🔄 Total attempts ({total_attempts}) reached limit - FORCING NEW SANDBOX")
        should_create_new_sandbox = True
    
    # If we need new sandbox, kill the old one
    if should_create_new_sandbox and _global_sandbox is not None:
        print("🔥 FORCING fresh sandbox due to too many failed attempts")
        _kill_existing_sandbox()
        _global_sandbox = None  # Ensure it's completely cleared
        _global_sandbox_info = {}
    
    # TRIGGER 3: Previous validation errors detected - BUT only if not in correction mode
    validation_result = ctx.get("validation_result", {})
    
    # FIX: Only kill sandbox if NOT in correction mode and we haven't already decided to create new one
    if (validation_result.get("errors") and 
        _global_sandbox is not None and 
        not is_correction and 
        not should_create_new_sandbox):
        print("🔥 Previous validation errors detected - creating fresh sandbox")
        _kill_existing_sandbox()
    
    # Now check if we have a working sandbox
    if _global_sandbox is not None:
        try:
            # Enhanced sandbox health check
            test_result = _global_sandbox.commands.run("echo 'test'", timeout=10)
            if test_result and test_result.stdout:
                # Additional health checks
                try:
                    # Check if Vite project exists
                    project_check = _global_sandbox.commands.run("ls my-app/package.json", timeout=5)
                    if project_check.exit_code != 0:
                        print("🔥 Project structure missing - creating fresh sandbox")
                        _kill_existing_sandbox()
                        return _get_or_create_persistent_sandbox(ctx, sandbox_timeout)
                        
                except Exception as health_error:
                    print(f"🔥 Sandbox health check failed: {health_error} - creating fresh sandbox")
                    _kill_existing_sandbox()
                    return _get_or_create_persistent_sandbox(ctx, sandbox_timeout)
                
                sandbox_id = getattr(_global_sandbox, "id", "unknown")
                print(f"✅ Reusing existing sandbox: {sandbox_id}")
                ctx["existing_sandbox_id"] = sandbox_id
                return _global_sandbox, False
        except Exception as e:
            print(f"⚠️ Sandbox is no longer alive: {e}")
            _global_sandbox = None
            _global_sandbox_info = {}
    
    # Create new sandbox if needed
    print("🆕 Creating NEW persistent sandbox...")
    new_sandbox = _create_sandbox_with_timeout(sandbox_timeout)
    
    _global_sandbox = new_sandbox
    sandbox_id = getattr(new_sandbox, "id", "unknown")
    _global_sandbox_info = {
        "id": sandbox_id,
        "created_at": time.time(),
        "project_setup": False,
        "session_id": current_session
    }
    
    ctx["existing_sandbox_id"] = sandbox_id
    print(f"✅ Created fresh sandbox: {sandbox_id}")
    return new_sandbox, True


def _is_project_setup() -> bool:
    """Check if the Vite project is already set up."""
    global _global_sandbox, _global_sandbox_info
    
    if not _global_sandbox or not _global_sandbox_info:
        return False
    
    if _global_sandbox_info.get("project_setup", False):
        print("✅ Project already set up (cached), skipping dependency installation")
        return True
    
    try:
        dir_check = _global_sandbox.commands.run("ls -la", timeout=10)
        if "my-app" not in (dir_check.stdout or ""):
            return False
            
        try:
            package_json = _global_sandbox.files.read("my-app/package.json")
            if not package_json or "vite" not in package_json:
                return False
        except Exception:
            return False
        
        try:
            node_modules_check = _global_sandbox.commands.run("ls -la my-app/", timeout=10)
            if "node_modules" not in (node_modules_check.stdout or ""):
                return False
        except Exception:
            return False
        
        _global_sandbox_info["project_setup"] = True
        print("✅ Project already set up, skipping dependency installation")
        return True
        
    except Exception as e:
        print(f"⚠️ Could not check project setup: {e}")
        return False


def _apply_file_corrections_only(correction_data: Dict[str, Any]) -> bool:
    """Apply ONLY file corrections to the existing sandbox with robust validation."""
    global _global_sandbox
    
    if not _global_sandbox:
        print("❌ No persistent sandbox available for corrections")
        return False
    
    try:
        print("🔧 Applying file corrections to existing sandbox...")
        
        # STEP 1: VALIDATE PROJECT STRUCTURE BEFORE CORRECTIONS
        if not _validate_project_structure(_global_sandbox):
            print("❌ Project structure invalid before corrections - cannot proceed")
            return False
        
        # STEP 2: BACKUP CRITICAL FILES
        backup_files = _backup_critical_files(_global_sandbox)
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
                    if not _validate_file_content(file_path, corrected_content):
                        print(f"   ⚠️ Content validation failed for {file_path}, skipping")
                        continue
                    
                    _global_sandbox.files.write(full_path, corrected_content)
                    print(f"   ✅ Updated: {file_path}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to update {file_path}: {e}")
                    # Restore from backup if available
                    if backup_files and file_path in backup_files:
                        _global_sandbox.files.write(full_path, backup_files[file_path])
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
                    _global_sandbox.files.write(full_path, content)
                    print(f"   ✅ Created: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to create {file_path}: {e}")
                    return False
        
        # STEP 5: VALIDATE PROJECT STRUCTURE AFTER CORRECTIONS
        if not _validate_project_structure(_global_sandbox):
            print("❌ Project structure corrupted after corrections - restoring from backup")
            if backup_files:
                _restore_from_backup(_global_sandbox, backup_files)
                print("🔄 Project restored from backup")
                return False
            else:
                print("❌ No backup available - project corrupted")
                return False
        
        # STEP 6: VALIDATE CRITICAL FILES
        if not _validate_critical_files(_global_sandbox):
            print("❌ Critical files corrupted after corrections")
            return False
        
        print("✅ All file corrections applied successfully with validation")
        return True
        
    except Exception as e:
        print(f"❌ Error applying file corrections: {e}")
        # Restore from backup if available
        if 'backup_files' in locals() and backup_files:
            _restore_from_backup(_global_sandbox, backup_files)
            print("🔄 Project restored from backup after error")
        return False


def _restart_dev_server_only(sandbox: Sandbox) -> Optional[str]:
    """Restart ONLY the dev server in the persistent sandbox, robustly."""
    global _global_sandbox
    
    # Add port definition
    port = int(os.getenv("E2B_VITE_PORT", "5173"))
    
    if not _global_sandbox:
        print("❌ No persistent sandbox available for dev server restart")
        return None
    
    print("🔄 Restarting dev server in existing sandbox...")
    try:
        # STEP 1: Validate project structure before restart
        if not _validate_project_structure(_global_sandbox):
            print("   ❌ Project structure invalid - cannot restart")
            return None
        
        # STEP 2: Validate corrected files
        print("   🔍 Validating corrected files before restart...")
        try:
            app_content = _global_sandbox.files.read("my-app/src/App.jsx")
            if not app_content or "function " not in app_content:
                print("   ⚠️ Invalid App.jsx, creating fallback")
                _create_fallback_react_app(_global_sandbox)
        except Exception:
            print("   ⚠️ Error reading App.jsx, creating fallback")
            _create_fallback_react_app(_global_sandbox)

        # STEP 3: Stop existing servers
        print("   🛑 Stopping existing dev server...")
        _global_sandbox.commands.run("bash -lc \"pkill -f 'npm run dev' || true\"", timeout=10)
        _global_sandbox.commands.run("bash -lc \"pkill -f 'vite' || true\"", timeout=10)

        import time as _t
        _t.sleep(2)

        # STEP 4: Clear caches
        _global_sandbox.commands.run("bash -lc \"cd my-app && rm -rf .vite node_modules/.vite dev.log || true\"", timeout=10)

        # STEP 5: Start dev server
        print("   🚀 Starting dev server...")
        _global_sandbox.commands.run(
            f"bash -lc \"cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &\"",
            timeout=30,
        )

        # STEP 6: Wait for server with reduced attempts
        if not _wait_for_http(_global_sandbox, port, max_attempts=5):
            print("   ⚠️ Dev server did not become ready after restart")
            return None

        host = _global_sandbox.get_host(port)
        url = f"https://{host}"
        print(f"   ✅ Dev server restarted at: {url}")
        return url

    except Exception as e:
        print(f"❌ Error restarting dev server: {e}")
        return None

def _install_package(sandbox: Sandbox, package_name: str) -> bool:
    """Install a single package with enhanced verification"""
    print(f"📦 Installing {package_name}...")
    try:
        # Run installation in the project directory
        command = f"cd my-app && npm install {package_name} --save"
        result = sandbox.commands.run(command, timeout=300)
        
        # Check installation success by exit code
        if result.exit_code != 0:
            print(f"   ❌ Installation failed with exit code {result.exit_code}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
        
        # Verify installation by checking package.json or node_modules
        verify_command = f"cd my-app && npm list {package_name} --depth=0"
        verify_result = sandbox.commands.run(verify_command, timeout=30)
        
        # FIX: Check the stdout property, not the object directly
        if verify_result.stdout and package_name in verify_result.stdout:
            print(f"   ✅ Verified {package_name} installation")
            return True
        else:
            print(f"   ❌ Installation verification failed for {package_name}")
            if verify_result.stdout:
                print(f"   npm list output: {verify_result.stdout}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error installing {package_name}: {e}")
        return False

def _detect_and_install_dependencies(sandbox: Sandbox, script_content: str) -> List[str]:
    print("🔍 Analyzing generated React code for dependencies...")
    
    # WHITELIST of allowed packages - ONLY these will be installed
    ALLOWED_PACKAGES = {
        'react-dom', 'lucide-react', 'react-icons', '@heroicons/react',
        'framer-motion', '@radix-ui/react-dialog', '@radix-ui/react-slot',
        'class-variance-authority', 'clsx', 'tailwind-merge'
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
        if _install_package(sandbox, package):
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


def _ensure_tailwind_build(sandbox) -> bool:
    """
    Ensure Tailwind CSS is properly built and ready.
    """
    print("🎨 Ensuring Tailwind CSS is properly built...")
    
    try:
        # Check if Tailwind config exists and is properly set up
        try:
            tailwind_config = sandbox.files.read("my-app/tailwind.config.js")
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
                sandbox.files.write("my-app/tailwind.config.js", fixed_config)
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
            sandbox.files.write("my-app/tailwind.config.js", config)
            print("✅ Created Tailwind config")
        
        # Ensure PostCSS config exists
        try:
            sandbox.files.read("my-app/postcss.config.js")
        except:
            print("⚠️ PostCSS config not found, creating...")
            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
            sandbox.files.write("my-app/postcss.config.js", postcss_config)
            print("✅ Created PostCSS config")
        
        # Force rebuild CSS by clearing Vite cache and rebuilding
        print("🔄 Clearing Vite cache and rebuilding...")
        sandbox.commands.run("cd my-app && rm -rf node_modules/.vite", timeout=10)
        sandbox.commands.run("cd my-app && rm -rf .vite", timeout=10)
        
        return True
        
    except Exception as e:
        print(f"❌ Error ensuring Tailwind build: {e}")
        return False


def _verify_css_content(sandbox: Sandbox) -> bool:
    """Verify CSS content is properly set up"""
    print("🔍 Verifying CSS content...")
    try:
        # 1. Check index.css contains Tailwind directives
        css_content = sandbox.files.read("my-app/src/index.css")
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
        main_content = sandbox.files.read("my-app/src/main.jsx")
        if "import './index.css'" not in main_content:
            print("❌ index.css import missing in main.jsx")
            return False
            
        print("✅ CSS content verified")
        return True
    except Exception as e:
        print(f"⚠️ CSS content verification failed: {e}")
        return False


# Main function
def apply_sandbox(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply Sandbox Node with SESSION-BASED sandbox management and EDIT support."""
    print("--- Running Apply Sandbox Node (Enhanced with Edit Support) ---")

    ctx = state.get("context", {}) or {}
    gen_result = ctx.get("generation_result", {}) or {}
    script_to_run = gen_result.get("e2b_script")
    is_correction = gen_result.get("is_correction", False)
    is_edit = gen_result.get("is_edit", False)
    
    # ADD SESSION ID TO CONTEXT
    session_id = state.get("session_id") or state.get("metadata", {}).get("session_id", "default")
    ctx["session_id"] = session_id

    if not script_to_run:
        msg = "No script to run in generation result"
        print(f"❌ {msg}")
        return {"error": msg}

    # HANDLE EDIT MODE - FIX: Check is_edit first
    if is_edit:
        print("🔄 EDIT MODE - Applying targeted changes to existing application...")
        
        # Get existing sandbox WITHOUT creating new one
        sandbox = _get_existing_sandbox_only(ctx)
        if not sandbox:
            print("❌ No existing sandbox found during edit - cannot proceed")
            print("   This usually means the initial generation didn't complete successfully")
            return {"error": "Edit failed - no existing sandbox. Please generate the initial design first."}
        
        # Apply edit changes
        correction_data = ctx.get("correction_data", {})
        if correction_data:
            if not _apply_edit_changes(correction_data):
                raise RuntimeError("Failed to apply edit changes")
            
            # Restart dev server with edits
            final_url = _restart_dev_server_only(sandbox)
            if not final_url:
                print("   ⚠️ Restart failed, trying full start...")
                port = int(os.getenv("E2B_VITE_PORT", "5173"))
                public_host = sandbox.get_host(port)
                _write_vite_config(sandbox, public_host, port)
                final_url = _start_dev_server(sandbox, port=port)
                if not final_url:
                    final_url = _start_preview_server(sandbox, port_primary=port, port_fallback=4173)
            
            # Success - CRITICAL FIX: Capture complete application state for proper storage
            sandbox_id = getattr(sandbox, "id", "unknown")
            
            # CRITICAL: Capture complete application state after successful edit
            complete_application_state = _capture_complete_application_state(sandbox)
            if complete_application_state:
                # Replace the edit-only generation_result with complete application state
                ctx["generation_result"] = complete_application_state
                print("✅ Replaced edit-only state with complete application state for proper storage")
            else:
                print("⚠️ Could not capture complete application state, keeping original edit state")
            
            ctx["sandbox_result"] = {
                "success": True,
                "url": final_url,
                "port": int(os.getenv("E2B_VITE_PORT", "5173")),
                "sandbox_id": sandbox_id,
                "message": "Edit changes applied successfully and server restarted"
            }
            state["context"] = ctx
            return state
        else:
            print("❌ No correction data found for edit mode")
            return {"error": "Edit failed - no correction data available"}
    
    # HANDLE CORRECTION MODE (existing logic)
    elif is_correction:
        print("🔄 CORRECTION MODE - Restarting Vite server with corrections...")
        
        # Get existing sandbox WITHOUT creating new one
        sandbox = _get_existing_sandbox_only(ctx)
        if not sandbox:
            print("❌ No existing sandbox found during correction - cannot proceed")
            return {"error": "Correction failed - no existing sandbox"}
        
        try:
            restart_result = _restart_dev_server_only(sandbox)
            if restart_result:
                print("✅ Vite server restarted successfully with corrections")
                return {"success": True, "message": "Corrections applied and server restarted"}
            else:
                print("❌ Failed to restart Vite server with corrections")
                return {"error": "Failed to restart server with corrections"}
        except Exception as e:
            print(f"❌ Error restarting Vite server: {e}")
            return {"error": f"Server restart failed: {e}"}

    if not os.getenv("E2B_API_KEY"):
        msg = "E2B_API_KEY is not set; please configure your environment."
        print(f"❌ {msg}")
        ctx["sandbox_result"] = {"success": False, "error": msg}
        state["context"] = ctx
        return state

    port = int(os.getenv("E2B_VITE_PORT", "5173"))
    sandbox_timeout = _get_sandbox_timeout()

    try:
        sandbox_timeout = int(os.getenv("E2B_SANDBOX_TIMEOUT", "3600"))
        
        # FIX: Mark context as correction mode BEFORE getting sandbox
        if is_correction:
            print("🔄 CORRECTION MODE - Using existing sandbox for targeted fixes...")
            ctx["is_correction"] = True  # MARK AS CORRECTION MODE
        
        # Get sandbox (will reuse existing if in correction mode)
        sandbox, newly_created = _get_or_create_persistent_sandbox(ctx, sandbox_timeout)
        
        if is_correction:
            correction_data = ctx.get("correction_data", {})
            if correction_data:
                if not _apply_file_corrections_only(correction_data):
                    raise RuntimeError("Failed to apply file corrections")
                
            final_url = _restart_dev_server_only(sandbox)  # ✅ Only 1 argument (port)
            if not final_url:
                print("   ⚠️ Restart failed, trying full start...")
                public_host = sandbox.get_host(port)
                _write_vite_config(sandbox, public_host, port)
                final_url = _start_dev_server(sandbox, port=port)
                if not final_url:
                    final_url = _start_preview_server(sandbox, port_primary=port, port_fallback=4173)
            
            # CRITICAL: If all restart attempts fail, stop the process
            if not final_url:
                print("❌ All restart attempts failed - stopping correction process")
                ctx["sandbox_result"] = {
                    "success": False,
                    "error": "Failed to restart dev server after correction",
                    "details": "Correction process stopped due to server restart failures"
                }
                state["context"] = ctx
                return state
        
        else:
            # INITIAL DEPLOYMENT MODE - normal flow
            print(" INITIAL DEPLOYMENT MODE...")
            
            try:
                sandbox.set_timeout(sandbox_timeout)
            except Exception:
                pass

            print(f"✅ Using sandbox: {ctx['existing_sandbox_id']}")

            if not _is_project_setup():
                print("Setting up the base Vite project environment...")
                if not _create_fast_vite_project(sandbox):
                    raise RuntimeError("Failed to create the base Vite project.")
                
                global _global_sandbox_info
                if _global_sandbox_info:
                    _global_sandbox_info["project_setup"] = True
            else:
                print("✅ Skipping dependency installation - project already set up")

            # Execute LLM script - ENHANCED ERROR HANDLING
            normalized = _normalize_e2b_api(script_to_run)
            print("Executing generated script to add UI components...")
            
            
            # 🚀 NEW: DETECT AND INSTALL DEPENDENCIES BEFORE SCRIPT EXECUTION
            print("🔍 Analyzing script for dependencies...")
            try:
                installed_packages = _detect_and_install_dependencies(sandbox, normalized)
                if installed_packages:
                    print(f"✅ Successfully installed {len(installed_packages)} packages: {', '.join(installed_packages)}")
                    # Give npm a moment to update package.json and node_modules
                    time.sleep(2)
                else:
                    print("✅ No additional packages needed to install")
            except Exception as dep_error:
                print(f"⚠️ Dependency detection failed: {dep_error}")
                print("Continuing with script execution anyway...")
            
            script_execution_success = False
            try:
                ns: Dict[str, Any] = {"Sandbox": Sandbox, "sandbox": sandbox}
                print("📝 Executing script in namespace...")
                exec(normalized, ns)
                
                print(f"🔍 Available functions in namespace: {list(ns.keys())}")
                
                # FIXED: Dynamically find the main function instead of hardcoding the name.
                # This handles cases where the LLM names it `create_reality_app` or something similar.
                main_function = None
                for key in ns:
                    if key.startswith("create_") and key.endswith("_app") and callable(ns[key]):
                        main_function = ns[key]
                        print(f"✅ Found main generator function: '{key}'")
                        break
                
                if main_function:
                    result = main_function(sandbox)
                    print(f"✅ Script execution result: {result}")
                    script_execution_success = True
                else:
                    print("❌ No valid generator function (e.g., create_react_app) found in the generated script.")
                    print(f"   Available keys in namespace: {list(ns.keys())}")

            except SyntaxError as syntax_error:
                print(f"❌ Script has syntax errors: {syntax_error}")
                print(f"Error on line {syntax_error.lineno}: {syntax_error.text}")
            
            except Exception as script_error:
                print(f"❌ Script execution failed with error: {script_error}")
                print(f"Error type: {type(script_error).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
            
            # Only create fallback if script execution actually failed
            if not script_execution_success:
                print("🔧 Script execution failed, creating fallback React app...")
                _create_fallback_react_app(sandbox)
                print("✅ Fallback React app created successfully")
            else:
                print("✅ Generated script executed successfully, no fallback needed")

            # NEW: Ensure Tailwind CSS is properly built
            print("🎨 Ensuring CSS is properly configured...")

            _ensure_css_files(sandbox)

            _fix_vite_css_processing(sandbox)

            if not _verify_css_content(sandbox):
                print("❌ Critical CSS verification failed! Recreating CSS files...")
                _ensure_css_files(sandbox)
                if not _verify_css_content(sandbox):
                    print("❌❌❌ CSS setup is fundamentally broken! Using fallback CSS")
                    sandbox.files.write("my-app/src/index.css", FALLBACK_CSS)  # pyright: ignore[reportUndefinedVariable]

            _validate_react_components(sandbox)
            _ensure_tailwind_cdn_in_index_html(sandbox)
            # Step 5: Clear all caches before starting server
            print("🧹 Final cache clear before server start...")
            sandbox.commands.run("cd my-app && rm -rf node_modules/.vite", timeout=10)
            sandbox.commands.run("cd my-app && rm -rf .vite", timeout=10)

            # Step 6: Start server normally
            public_host = sandbox.get_host(port)
            _write_vite_config(sandbox, public_host, port)

            final_url = _start_dev_server(sandbox)
            if final_url is None:
                final_url = _start_preview_server(sandbox, port_primary=port, port_fallback=4173)

        if not final_url:
            raise RuntimeError("Dev server not accessible. Check logs.")

        sandbox_id = getattr(sandbox, "id", "unknown")
        
        ctx["sandbox_result"] = {
            "success": True,
            "url": final_url,
            "port": port,
            "sandbox_id": sandbox_id,
            "message": "Application deployed successfully with auto-dependency installation"
        }

    except Exception as e:
        print(f"❌ Sandbox application failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        ctx["sandbox_result"] = {
            "success": False,
            "error": str(e),
            "details": "Failed to apply code to sandbox with enhanced dependency detection"
        }

    state["context"] = ctx
    return state

def _capture_complete_application_state(sandbox) -> Dict[str, Any]:
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
            src_files_result = sandbox.commands.run("find my-app/src -name '*.jsx' -o -name '*.js' -o -name '*.css'", timeout=10)
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
                content = sandbox.files.read(full_path)
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

def _try_alternative_postcss_setup(sandbox: Sandbox) -> bool:
    """Try alternative PostCSS setup if the main one fails"""
    print("🔄 TRYING ALTERNATIVE POSTCSS SETUP...")
    
    try:
        # Method 1: Use the fallback config
        print("📝 Switching to fallback PostCSS config...")
        sandbox.commands.run("cd my-app && mv postcss.config.fallback.js postcss.config.js", timeout=5)
        
        # Method 2: If that doesn't work, try CommonJS format
        print("📝 Creating CommonJS PostCSS config...")
        commonjs_postcss = """module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        sandbox.files.write("my-app/postcss.config.cjs", commonjs_postcss)
        
        # Method 3: Try without the separate plugin
        print("📝 Creating simple PostCSS config...")
        simple_postcss = """export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        sandbox.files.write("my-app/postcss.config.simple.js", simple_postcss)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in alternative PostCSS setup: {e}")
        return False


def _fix_vite_css_processing(sandbox: Sandbox) -> bool:
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
        
        sandbox.files.write("my-app/vite.config.js", vite_config)
        print("✅ Updated Vite config for CDN-based Tailwind")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Vite CSS processing: {e}")
        return False

def _validate_project_structure(sandbox: Sandbox) -> bool:
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
            content = sandbox.files.read(file_path)
            if not content:
                print(f"❌ Critical file empty: {file_path}")
                return False
        except Exception as e:
            print(f"❌ Critical file missing: {file_path} - {e}")
            return False
    
    # Check if npm commands work
    try:
        result = sandbox.commands.run("cd my-app && npm --version", timeout=10)
        if result.exit_code != 0:
            print("❌ npm not working in project directory")
            return False
    except Exception as e:
        print(f"❌ Cannot verify npm: {e}")
        return False
    
    print("✅ Project structure validation passed")
    return True

def _validate_critical_files(sandbox: Sandbox) -> bool:
    """Validate that critical files contain valid content."""
    print("🔍 Validating critical file contents...")
    
    try:
        # Check App.jsx has valid React component
        app_content = sandbox.files.read("my-app/src/App.jsx")
        if not app_content or "function " not in app_content or "export default" not in app_content:
            print("❌ App.jsx is not a valid React component")
            return False
        
        # Check main.jsx has proper imports
        main_content = sandbox.files.read("my-app/src/main.jsx")
        if not main_content or "import App" not in main_content:
            print("❌ main.jsx missing App import")
            return False
        
        # Check package.json has required fields
        package_content = sandbox.files.read("my-app/package.json")
        if not package_content or "dependencies" not in package_content:
            print("❌ package.json missing dependencies")
            return False
        
        print("✅ Critical file validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating critical files: {e}")
        return False

def _backup_critical_files(sandbox: Sandbox) -> Dict[str, str]:
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
            content = sandbox.files.read(file_path)
            if content:
                backup_files[file_path] = content
                print(f"   ✅ Backed up: {file_path}")
        except Exception as e:
            print(f"   ⚠️ Could not backup {file_path}: {e}")
    
    print(f"🔄 Backup created for {len(backup_files)} files")
    return backup_files

def _restore_from_backup(sandbox: Sandbox, backup_files: Dict[str, str]) -> bool:
    """Restore project from backup files."""
    print("🔄 Restoring project from backup...")
    
    try:
        for file_path, content in backup_files.items():
            try:
                sandbox.files.write(file_path, content)
                print(f"   ✅ Restored: {file_path}")
            except Exception as e:
                print(f"   ❌ Failed to restore {file_path}: {e}")
                return False
        
        print("✅ Project restored from backup successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error restoring from backup: {e}")
        return False

def _validate_file_content(file_path: str, content: str) -> bool:
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

def _get_existing_sandbox_only(ctx: Dict[str, Any]):
    """Get existing sandbox ONLY - never create new one during corrections."""
    global _global_sandbox, _global_sandbox_info
    
    if _global_sandbox is None:
        return None
    
    try:
        # Quick health check
        test_result = _global_sandbox.commands.run("echo 'test'", timeout=5)
        if test_result and test_result.stdout:
            sandbox_id = getattr(_global_sandbox, "id", "unknown")
            print(f"✅ Using existing sandbox for corrections: {sandbox_id}")
            return _global_sandbox
    except Exception as e:
        print(f"⚠️ Existing sandbox is not healthy: {e}")
        return None
    
    return None

def _apply_edit_changes(correction_data: Dict[str, Any]) -> bool:
    """Apply edit changes to the existing sandbox with robust validation and dependency installation."""
    global _global_sandbox
    
    if not _global_sandbox:
        print("❌ No persistent sandbox available for edits")
        return False
    
    try:
        print("🔧 Applying edit changes to existing sandbox...")
        
        # STEP 1: VALIDATE PROJECT STRUCTURE BEFORE EDITS
        if not _validate_project_structure(_global_sandbox):
            print("❌ Project structure invalid before edits - cannot proceed")
            return False
        
        # STEP 2: BACKUP CRITICAL FILES
        backup_files = _backup_critical_files(_global_sandbox)
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
                installed_packages = _detect_and_install_dependencies(_global_sandbox, combined_content)
                if installed_packages:
                    print(f"✅ Successfully installed {len(installed_packages)} new packages: {', '.join(installed_packages)}")
                    # Give npm a moment to update package.json and node_modules
                    time.sleep(2)
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
                    if not _validate_file_content(file_path, corrected_content):
                        print(f"   ⚠️ Content validation failed for {file_path}, skipping")
                        continue
                    
                    # CRITICAL: Write the modified content
                    _global_sandbox.files.write(full_path, corrected_content)
                    print(f"   ✅ Updated: {file_path}")
                    
                    # Verify the change was applied
                    verify_content = _global_sandbox.files.read(full_path)
                    if verify_content == corrected_content:
                        print(f"   ✅ Verified: {file_path} updated successfully")
                    else:
                        print(f"   ⚠️ Warning: {file_path} content may not have updated correctly")
                    
                except Exception as e:
                    print(f"   ❌ Failed to update {file_path}: {e}")
                    # Restore from backup if available
                    if backup_files and file_path in backup_files:
                        _global_sandbox.files.write(full_path, backup_files[file_path])
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
                    _global_sandbox.files.write(full_path, content)
                    print(f"   ✅ Created: {file_path}")
                except Exception as e:
                    print(f"   ❌ Failed to create {file_path}: {e}")
                    return False
        
        # STEP 7: VALIDATE PROJECT STRUCTURE AFTER EDITS
        if not _validate_project_structure(_global_sandbox):
            print("❌ Project structure corrupted after edits - restoring from backup")
            if backup_files:
                _restore_from_backup(_global_sandbox, backup_files)
                print("🔄 Project restored from backup")
                return False
            else:
                print("❌ No backup available - project corrupted")
                return False
        
        # STEP 8: VALIDATE CRITICAL FILES
        if not _validate_critical_files(_global_sandbox):
            print("❌ Critical files corrupted after edits")
            return False
        
        print("✅ All edit changes applied successfully with validation")
        return True
        
    except Exception as e:
        print(f"❌ Error applying edit changes: {e}")
        # Restore from backup if available
        if 'backup_files' in locals() and backup_files:
            _restore_from_backup(_global_sandbox, backup_files)
            print("🔄 Project restored from backup after error")
        return False
