import os
import re
import time
from typing import Dict, Any, Optional, List


from e2b_code_interpreter import Sandbox


import threading
from typing import Dict, Any


_session_sandboxes: Dict[str, Dict[str, Any]] = {}
_sandbox_lock = threading.Lock()

import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

_session_exec_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


_executor = ThreadPoolExecutor(max_workers=10)


async def _async_sandbox_command(sandbox, command: str, timeout: int = 30):
    """Run sandbox command asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, lambda: sandbox.commands.run(command, timeout=timeout)
    )


async def _async_sandbox_file_write(sandbox, path: str, content: str):
    """Write file asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, lambda: sandbox.files.write(path, content)
    )


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


def _normalize_e2b_api(src: str) -> str:
    """
    Convert any legacy generator script to current E2B SDK surface.
    Also removes markdown code blocks that some LLMs add.
    """
    import re

    if "```python" in src:

        code_match = re.search(r"```python\s*(.*?)\s*```", src, re.DOTALL)
        if code_match:
            src = code_match.group(1)
    elif "```" in src:

        src = re.sub(r"```[^\n]*\n", "", src)
        src = re.sub(r"\n```", "", src)

    src = src.replace("sandbox.filesystem.", "sandbox.files.")

    src = re.sub(
        r"sandbox\.process\.start_and_wait\((.*?)\)",
        r"sandbox.commands.run(\1)",
        src,
        flags=re.DOTALL,
    )

    src = re.sub(
        r"sandbox\.process\.start\((.*?)\)",
        r"sandbox.commands.run(\1, background=True)",
        src,
        flags=re.DOTALL,
    )

    src = src.replace("sandbox.get_hostname", "sandbox.get_host")

    if "create_react_app(None)" in src:
        src = src.replace("create_react_app(None)", "")

    src = re.sub(r"create_react_app\([^)]*\)\s*$", "", src, flags=re.MULTILINE)

    return src


def _get_sandbox_timeout() -> int:
    """Reads E2B_TIMEOUT and returns a safe value (1..3600)."""
    max_allowed = 3600
    default = 600
    raw = os.getenv("E2B_TIMEOUT", str(default))
    try:
        val = int(raw)
    except Exception:

        return default
    if val <= 0:

        return default
    if val > max_allowed:

        return max_allowed
    return val


async def _create_fast_vite_project(sandbox) -> bool:
    """Create a Vite + React project with CDN Tailwind."""
    try:
        await _async_sandbox_command(
            sandbox, "npm create vite@latest my-app -- --template react", 180
        )
        await _async_sandbox_command(sandbox, "cd my-app && npm install", 300)

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

        return True

    except Exception as e:

        return False


async def _ensure_css_files(sandbox: Sandbox):

    try:

        index_css_path = "my-app/src/index.css"

        css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        await _async_sandbox_file_write(sandbox, index_css_path, css_content)

        main_jsx_path = "my-app/src/main.jsx"
        main_content = await _async_sandbox_file_read(sandbox, main_jsx_path)
        if (
            "import App from './App.jsx';" in main_content
            and "import './index.css'" not in main_content
        ):
            main_content = main_content.replace(
                "import App from './App.jsx';",
                "import App from './App.jsx';\nimport './index.css';",
            )
            await _async_sandbox_file_write(sandbox, main_jsx_path, main_content)

    except Exception as e:
        print(f"❌ Error ensuring CSS files: {e}")


async def _ensure_tailwind_cdn_in_index_html(sandbox: Sandbox) -> bool:

    try:
        path = "my-app/index.html"
        html = await _async_sandbox_file_read(sandbox, path)
    except Exception as e:

        return False

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

        html = re.sub(
            r"<script[^>]*cdn\.tailwindcss\.com[^>]*>.*?</script>",
            "",
            html,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<script[^>]*window\.tailwind[^>]*>.*?</script>", "", html, flags=re.DOTALL
        )

        if "</head>" in html:
            html = html.replace("</head>", f"{inject}\n</head>")
        else:
            html = inject + "\n" + html

        await _async_sandbox_file_write(sandbox, path, html)

        return True
    except Exception as e:

        return False


async def _write_vite_config(sandbox, public_host: str, port: int) -> None:
    """Fixed Vite config for E2B."""

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

    except Exception as e:
        print(f"⚠️ Could not write vite config: {e}")


async def _wait_for_http(sandbox, port: int, max_attempts: int = 30) -> bool:
    """Wait for HTTP server to be ready - FIXED VERSION."""

    for attempt in range(1, max_attempts + 1):
        try:
            result = await _async_sandbox_command(
                sandbox,
                f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}",
                10,
            )
            if result and result.stdout:
                response_code = result.stdout.strip()

                if response_code and response_code != "000" and response_code != "":

                    return True
        except Exception as e:
            print(f"   Attempt {attempt}: Error checking server: {e}")

        if attempt < max_attempts:
            await asyncio.sleep(3)

    return False


async def _start_dev_server(sandbox, port: int = 5173) -> Optional[str]:
    """Start the Vite dev server."""

    try:
        await _async_sandbox_command(
            sandbox,
            f'bash -lc "cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &"',
        )

        if not await _wait_for_http(sandbox, port):

            return None

        host = sandbox.get_host(port)
        url = f"https://{host}"

        return url

    except Exception as e:

        return None


async def _start_preview_server(
    sandbox, port_primary: int = 5173, port_fallback: int = 4173
) -> Optional[str]:
    """Build and start Vite preview."""

    try:
        await _async_sandbox_command(sandbox, "cd my-app && npm run build", 480)

        await _async_sandbox_command(
            sandbox,
            f'bash -lc "cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_primary} > preview.log 2>&1 &"',
        )
        if await _wait_for_http(sandbox, port_primary):
            host = sandbox.get_host(port_primary)
            return f"https://{host}"

        await _async_sandbox_command(
            sandbox,
            f'bash -lc "cd my-app && nohup npm run preview -- --host 0.0.0.0 --port {port_fallback} > preview_fallback.log 2>&1 &"',
        )
        if await _wait_for_http(sandbox, port_fallback):
            host = sandbox.get_host(port_fallback)
            return f"https://{host}"

        return None

    except Exception as e:

        return None


async def _create_sandbox_with_timeout(timeout_s: int):
    """Create a sandbox with timeout handling asynchronously."""
    try:
        loop = asyncio.get_event_loop()
        if hasattr(Sandbox, "create"):
            template_id = os.getenv("E2B_TEMPLATE_ID")
            if template_id:
                return await loop.run_in_executor(
                    None,
                    lambda: Sandbox.create(template=template_id, timeout=timeout_s),
                )
            return await loop.run_in_executor(
                None, lambda: Sandbox.create(timeout=timeout_s)
            )
        return await loop.run_in_executor(None, lambda: Sandbox(timeout=timeout_s))
    except Exception as e:
        msg = str(e)
        if (
            "Timeout cannot be greater than" in msg
            or "1 hours" in msg
            or "1 hour" in msg
        ):

            loop = asyncio.get_event_loop()
            if hasattr(Sandbox, "create"):
                template_id = os.getenv("E2B_TEMPLATE_ID")
                if template_id:
                    return await loop.run_in_executor(
                        None, lambda: Sandbox.create(template=template_id, timeout=3600)
                    )
                return await loop.run_in_executor(
                    None, lambda: Sandbox.create(timeout=3600)
                )
            return await loop.run_in_executor(None, lambda: Sandbox(timeout=3600))
        raise


async def _create_fallback_react_app(sandbox) -> None:
    """Create a working fallback React app - ENHANCED VERSION."""

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

    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Inter', sans-serif;
}"""

    await _async_sandbox_file_write(sandbox, "my-app/src/index.css", index_css)

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


async def _validate_react_components(sandbox) -> None:
    """Validate and fix React components."""
    try:

        try:
            app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")

            issues = []
            if "import React" not in app_content and "React" in app_content:
                issues.append("Missing React import")
            if "export default" not in app_content:
                issues.append("Missing export default")
            if "function " not in app_content and "const " not in app_content:
                issues.append("No component function found")

            if issues:

                await _create_fallback_react_app(sandbox)
            else:
                print("✅ React component validation passed")

        except Exception as e:

            await _create_fallback_react_app(sandbox)

    except Exception as e:
        print(f"⚠️ Component validation failed: {e}")


def _kill_sandbox_for_session(session_id: str):
    """Kill sandbox for a specific session."""
    with _sandbox_lock:
        if session_id in _session_sandboxes:
            sandbox_info = _session_sandboxes[session_id]
            sandbox = sandbox_info.get("sandbox")
            if sandbox:
                try:

                    sandbox.kill()

                except Exception as e:
                    print(f"⚠️ Error terminating sandbox for session {session_id}: {e}")
            del _session_sandboxes[session_id]


import asyncio, time


async def _get_or_create_persistent_sandbox(ctx: Dict[str, Any], sandbox_timeout: int):
    """Get or create sandbox for this session WITHOUT awaiting inside the global lock."""
    session_id = ctx.get("session_id", "default")

    with _sandbox_lock:
        entry = _session_sandboxes.get(session_id)
        sandbox = entry.get("sandbox") if entry else None

    if sandbox:
        try:
            ping = await _async_sandbox_command(sandbox, "echo ok", 5)
            proj = await _async_sandbox_command(sandbox, "ls my-app/package.json", 5)
            if (
                getattr(ping, "exit_code", 1) == 0
                and getattr(proj, "exit_code", 1) == 0
            ):
                ctx["existing_sandbox_id"] = getattr(sandbox, "id", "unknown")
                return sandbox, False
        except Exception:
            pass

        with _sandbox_lock:
            _session_sandboxes.pop(session_id, None)

    new_sandbox = await _create_sandbox_with_timeout(sandbox_timeout)
    info = {
        "id": getattr(new_sandbox, "id", "unknown"),
        "created_at": time.time(),
        "project_setup": False,
        "session_id": session_id,
    }

    with _sandbox_lock:
        _session_sandboxes[session_id] = {"sandbox": new_sandbox, "info": info}

    ctx["existing_sandbox_id"] = info["id"]

    return new_sandbox, True


async def _is_project_setup(session_id: str) -> bool:
    """Check if project is set up for this session without awaiting under the lock."""

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

        with _sandbox_lock:
            if session_id in _session_sandboxes:
                _session_sandboxes[session_id]["info"]["project_setup"] = True
        return True
    except Exception as e:

        return False


async def _apply_file_corrections_only(
    correction_data: Dict[str, Any], session_id: str
) -> bool:
    """Apply ONLY file corrections to the existing sandbox with robust validation."""
    sandbox = _get_session_sandbox(session_id)

    if not sandbox:

        return False

    try:

        if not await _validate_project_structure(sandbox):

            return False

        backup_files = await _backup_critical_files(sandbox)
        if not backup_files:
            print("⚠️ Could not backup critical files, proceeding with caution")

        files_to_correct = correction_data.get("files_to_correct", [])
        for file_correction in files_to_correct:
            file_path = file_correction.get("path", "")
            corrected_content = file_correction.get("corrected_content", "")

            if file_path and corrected_content:

                full_path = (
                    f"my-app/{file_path}"
                    if not file_path.startswith("my-app/")
                    else file_path
                )

                try:

                    if not await _validate_file_content(file_path, corrected_content):

                        continue

                    await _async_sandbox_file_write(
                        sandbox, full_path, corrected_content
                    )

                except Exception as e:

                    if backup_files and file_path in backup_files:
                        await _async_sandbox_file_write(
                            sandbox, full_path, backup_files[file_path]
                        )

                    return False

        new_files = correction_data.get("new_files", [])
        for file_info in new_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")

            if file_path and content:

                full_path = (
                    f"my-app/{file_path}"
                    if not file_path.startswith("my-app/")
                    else file_path
                )

                try:
                    await _async_sandbox_file_write(sandbox, full_path, content)

                except Exception as e:

                    return False

        if not await _validate_project_structure(sandbox):

            if backup_files:
                await _restore_from_backup(sandbox, backup_files)

                return False
            else:

                return False

        if not await _validate_critical_files(sandbox):

            return False

        return True

    except Exception as e:

        if "backup_files" in locals() and backup_files:
            await _restore_from_backup(sandbox, backup_files)

        return False


async def _restart_dev_server_only(session_id: str) -> Optional[str]:
    """Restart ONLY the dev server in the persistent sandbox, robustly."""
    sandbox = _get_session_sandbox(session_id)

    port = int(os.getenv("E2B_VITE_PORT", "5173"))

    if not sandbox:

        return None

    try:

        if not await _validate_project_structure(sandbox):

            return None

        try:
            app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")
            if not app_content or "function " not in app_content:

                await _create_fallback_react_app(sandbox)
        except Exception:

            await _create_fallback_react_app(sandbox)

        await _async_sandbox_command(
            sandbox, "bash -lc \"pkill -f 'npm run dev' || true\"", 10
        )
        await _async_sandbox_command(
            sandbox, "bash -lc \"pkill -f 'vite' || true\"", 10
        )

        import time as _t

        await asyncio.sleep(2)

        await _async_sandbox_command(
            sandbox,
            'bash -lc "cd my-app && rm -rf .vite node_modules/.vite dev.log || true"',
            10,
        )

        await _async_sandbox_command(
            sandbox,
            f'bash -lc "cd my-app && nohup npm run dev -- --host 0.0.0.0 --port {port} > dev.log 2>&1 &"',
            timeout=30,
        )

        if not await _wait_for_http(sandbox, port, max_attempts=5):

            return None

        host = sandbox.get_host(port)
        url = f"https://{host}"

        return url

    except Exception as e:

        return None


async def _install_package(sandbox: Sandbox, package_name: str) -> bool:
    """Install a single package with enhanced verification"""

    try:

        command = f"cd my-app && npm install {package_name} --save"
        result = await _async_sandbox_command(sandbox, command, 300)

        if result.exit_code != 0:

            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False

        verify_command = f"cd my-app && npm list {package_name} --depth=0"
        verify_result = await _async_sandbox_command(sandbox, verify_command, 30)

        if (
            verify_result
            and verify_result.stdout
            and package_name in verify_result.stdout
        ):

            return True
        else:

            if verify_result and verify_result.stdout:
                print(f"   npm list output: {verify_result.stdout}")
            return False

    except Exception as e:

        return False


async def _detect_and_install_dependencies(
    sandbox: Sandbox, script_content: str
) -> List[str]:

    ALLOWED_PACKAGES = {
        "react-dom",
        "react-router-dom",
        "react-router",
        "lucide-react",
        "react-icons",
        "@heroicons/react",
        "@tabler/icons-react",
        "feather-react",
        "react-feather",
        "framer-motion",
        "react-spring",
        "react-transition-group",
        "lottie-react",
        "react-spring-web",
        "@radix-ui/react-dialog",
        "@radix-ui/react-slot",
        "@radix-ui/react-dropdown-menu",
        "@radix-ui/react-tooltip",
        "@radix-ui/react-popover",
        "@radix-ui/react-select",
        "@radix-ui/react-checkbox",
        "@radix-ui/react-radio-group",
        "@radix-ui/react-switch",
        "@radix-ui/react-tabs",
        "@radix-ui/react-accordion",
        "@radix-ui/react-alert-dialog",
        "@radix-ui/react-avatar",
        "@radix-ui/react-badge",
        "@radix-ui/react-button",
        "@radix-ui/react-card",
        "@radix-ui/react-carousel",
        "@radix-ui/react-collapsible",
        "@radix-ui/react-context-menu",
        "@radix-ui/react-hover-card",
        "@radix-ui/react-label",
        "@radix-ui/react-menubar",
        "@radix-ui/react-navigation-menu",
        "@radix-ui/react-progress",
        "@radix-ui/react-scroll-area",
        "@radix-ui/react-separator",
        "@radix-ui/react-sheet",
        "@radix-ui/react-slider",
        "@radix-ui/react-toast",
        "@radix-ui/react-toggle",
        "@radix-ui/react-toggle-group",
        "class-variance-authority",
        "clsx",
        "tailwind-merge",
        "classnames",
        "styled-components",
        "@emotion/react",
        "@emotion/styled",
        "stitches",
        "vanilla-extract",
        "react-hook-form",
        "@hookform/resolvers",
        "zod",
        "yup",
        "formik",
        "react-final-form",
        "zustand",
        "jotai",
        "recoil",
        "redux",
        "@reduxjs/toolkit",
        "react-query",
        "@tanstack/react-query",
        "swr",
        "axios",
        "ky",
        "fetch-retry",
        "react-query",
        # Date & Time
        "date-fns",
        "dayjs",
        "moment",
        "react-datepicker",
        "react-day-picker",
        "react-calendar",
        # Charts & Data Visualization
        "recharts",
        "chart.js",
        "react-chartjs-2",
        "victory",
        "d3",
        "react-d3-tree",
        "react-vis",
        # Utility Libraries
        "lodash",
        "lodash-es",
        "ramda",
        "immer",
        "uuid",
        "nanoid",
        "crypto-js",
        # Media & File Handling
        "react-dropzone",
        "react-image-crop",
        "react-image-gallery",
        "react-player",
        "react-audio-player",
        # Layout & Grid
        "react-grid-layout",
        "react-masonry-css",
        "react-virtualized",
        "react-window",
        "react-virtual",
        # Notifications & Feedback
        "react-hot-toast",
        "react-toastify",
        "react-notifications",
        "react-alert",
        "react-confirm-alert",
        # Accessibility
        "react-aria",
        "react-spectrum",
        "react-focus-lock",
        "react-remove-scroll",
        "react-modal",
        # Development & Debugging
        "react-error-boundary",
        "react-helmet",
        "react-helmet-async",
        "react-intersection-observer",
        "react-use",
        # Mobile & Touch
        "react-swipeable",
        "react-touch-dnd",
        "react-gesture-responder",
        # Maps & Location
        "react-leaflet",
        "react-map-gl",
        "google-map-react",
        # Code & Syntax Highlighting
        "react-syntax-highlighter",
        "prism-react-renderer",
        "highlight.js",
        # PDF & Document
        "react-pdf",
        "react-file-viewer",
        "react-document-viewer",
        # Social & Sharing
        "react-share",
        "react-social-sharing",
        "react-facebook-pixel",
        # Analytics & Tracking
        "react-ga",
        "react-ga4",
        "react-gtm",
        # Testing Utilities (for development)
        "@testing-library/react",
        "@testing-library/jest-dom",
        "react-testing-library",
        # Build & Bundle
        "react-refresh",
        "react-fast-refresh",
    }

    potential_packages = set()

    patterns = [
        r'import\s+.*?from\s+["\']([^"\'.\s/][^"\']*)["\']',
        r'import\s+["\']([^"\'.\s/][^"\']*)["\']',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, script_content)
        for match in matches:

            if not match.startswith(".") and not match.startswith("/"):
                package_name = match
                if package_name in ALLOWED_PACKAGES:
                    potential_packages.add(package_name)
                else:

                    if "/" in package_name:
                        root_package = "/".join(package_name.split("/")[:2])
                        if root_package in ALLOWED_PACKAGES:
                            potential_packages.add(root_package)
                        else:
                            print(
                                f"⚠️ Skipping blocked package: {package_name} (not in whitelist)"
                            )
                    else:
                        print(
                            f"⚠️ Skipping blocked package: {package_name} (not in whitelist)"
                        )

    builtin_packages = {"path", "fs", "os", "child_process", "react"}
    packages_to_install = [
        pkg for pkg in potential_packages if pkg not in builtin_packages
    ]

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

    file_write_pattern = r'sandbox\.files\.write\(["\']([^"\']+)["\'],\s*([^)]+)\)'
    matches = re.findall(file_write_pattern, script, re.DOTALL)

    for file_path, content_var in matches:

        content_pattern = rf'{re.escape(content_var)}\s*=\s*["\'\`]([^"\'\`]*)["\'\`]'
        content_match = re.search(content_pattern, script, re.DOTALL)
        if content_match:
            files[file_path] = content_match.group(1)

    return files


async def _ensure_tailwind_build(sandbox) -> bool:
    """
    Ensure Tailwind CSS is properly built and ready.
    """

    try:

        try:
            tailwind_config = await _async_sandbox_file_read(
                sandbox, "my-app/tailwind.config.js"
            )
            if "content:" not in tailwind_config:

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
                await _async_sandbox_file_write(
                    sandbox, "my-app/tailwind.config.js", fixed_config
                )

        except:

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
            await _async_sandbox_file_write(
                sandbox, "my-app/tailwind.config.js", config
            )

        try:
            await _async_sandbox_file_read(sandbox, "my-app/postcss.config.js")
        except:

            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""
            await _async_sandbox_file_write(
                sandbox, "my-app/postcss.config.js", postcss_config
            )

        await _async_sandbox_command(
            sandbox, "cd my-app && rm -rf node_modules/.vite", 10
        )
        await _async_sandbox_command(sandbox, "cd my-app && rm -rf .vite", 10)

        return True

    except Exception as e:

        return False


async def _verify_css_content(sandbox: Sandbox) -> bool:
    """Verify CSS content is properly set up"""

    try:

        css_content = await _async_sandbox_file_read(sandbox, "my-app/src/index.css")
        if "@tailwind base" not in css_content:

            return False
        if "@tailwind components" not in css_content:

            return False
        if "@tailwind utilities" not in css_content:

            return False

        main_content = await _async_sandbox_file_read(sandbox, "my-app/src/main.jsx")
        if "import './index.css'" not in main_content:

            return False

        return True
    except Exception as e:

        return False


# Main function
import time


async def apply_sandbox(state: Dict[str, Any]) -> Dict[str, Any]:
    """Apply Sandbox Node with SESSION-BASED sandbox management and robust EDIT support."""

    ctx = state.get("context", {}) or {}

    session_id = state.get("session_id") or state.get("metadata", {}).get(
        "session_id", "default"
    )
    ctx["session_id"] = session_id
    state["context"] = ctx

    lock = _session_exec_locks[session_id]
    async with lock:
        gen_result = ctx.get("generation_result", {}) or {}
        script_to_run = gen_result.get("e2b_script")
        is_correction = gen_result.get("is_correction", False)
        is_edit = gen_result.get("is_edit", False)
        port = int(os.getenv("E2B_VITE_PORT", "5173"))
        sandbox_timeout = int(os.getenv("E2B_SANDBOX_TIMEOUT", "3600"))
        if is_edit:

            sandbox = await _get_existing_sandbox_only(ctx)
            if not sandbox:
                msg = "No existing sandbox found during edit - cannot apply changes"

                return {"error": msg}

            correction_data = ctx.get("correction_data", {})
            if not correction_data:
                msg = "No correction data found for edit mode"

                return {"error": msg}

            if not await _apply_edit_changes(correction_data, session_id):
                raise RuntimeError("Failed to apply edit changes")

            final_url = await _restart_dev_server_only(session_id)
            if not final_url:

                public_host = sandbox.get_host(port)
                await _write_vite_config(sandbox, public_host, port)
                try:

                    async with asyncio.timeout(180):

                        final_url = await _start_preview_server(
                            sandbox, port_primary=port, port_fallback=4173
                        )
                        if not final_url:
                            final_url = await _start_dev_server(sandbox, port=port)

                except TimeoutError:

                    _kill_sandbox_for_session(session_id)
                    ctx["sandbox_failed"] = True
                    ctx["sandbox_error"] = "Timeout waiting for dev server"
                    state["context"] = ctx
                    return state

                if not final_url:

                    _kill_sandbox_for_session(session_id)
                    ctx["sandbox_failed"] = True
                    ctx["sandbox_error"] = "Dev server failed"
                    state["context"] = ctx
                    return state

            sandbox_id = getattr(sandbox, "id", "unknown")
            complete_state = await _capture_complete_application_state(sandbox)
            if complete_state:
                ctx["generation_result"] = complete_state

            ctx["sandbox_result"] = {
                "success": True,
                "url": final_url,
                "port": port,
                "sandbox_id": sandbox_id,
                "message": "Edit changes applied successfully and server restarted",
            }
            state["context"] = ctx
            return state

        if is_correction:

            sandbox = await _get_existing_sandbox_only(ctx)
            if not sandbox:
                return {"error": "Correction failed - no existing sandbox found"}
            try:
                restart_result = await _restart_dev_server_only(session_id)
                if restart_result:

                    return {
                        "success": True,
                        "message": "Corrections applied and server restarted",
                    }
                else:

                    public_host = sandbox.get_host(port)
                    await _write_vite_config(sandbox, public_host, port)
                    final_url = await _start_dev_server(sandbox, port=port)
                    if not final_url:
                        final_url = await _start_preview_server(
                            sandbox, port_primary=port, port_fallback=4173
                        )
                    return {"success": bool(final_url), "url": final_url}
            except Exception as e:

                return {"error": str(e)}

        if not script_to_run:
            msg = "No script to run in generation result"

            return {"error": msg}

        if not os.getenv("E2B_API_KEY"):
            msg = "E2B_API_KEY is not set; please configure your environment."

            ctx["sandbox_result"] = {"success": False, "error": msg}
            state["context"] = ctx
            return state

        try:
            sandbox, newly_created = await _get_or_create_persistent_sandbox(
                ctx, sandbox_timeout
            )

            if not await _is_project_setup(session_id):

                if not await _create_fast_vite_project(sandbox):
                    raise RuntimeError("Failed to create base Vite project")
                with _sandbox_lock:
                    if session_id in _session_sandboxes:
                        _session_sandboxes[session_id]["info"]["project_setup"] = True
            else:
                print("✅ Project already set up")

            normalized = _normalize_e2b_api(script_to_run)

            try:
                installed_packages = await _detect_and_install_dependencies(
                    sandbox, normalized
                )
                if installed_packages:

                    await asyncio.sleep(2)
                else:
                    print("✅ No additional packages required")
            except Exception as dep_error:
                print(f"⚠️ Dependency detection failed: {dep_error}")

            script_execution_success = False
            try:
                ns: Dict[str, Any] = {"Sandbox": Sandbox, "sandbox": sandbox}
                exec(normalized, ns)

                main_function = None
                for key in ns:
                    if (
                        key.startswith("create_")
                        and key.endswith("_app")
                        and callable(ns[key])
                    ):
                        main_function = ns[key]

                        break

                if main_function:
                    result = main_function(sandbox)

                    script_execution_success = True
                else:
                    print("❌ No generator function found in script output")

            except Exception as e:
                import traceback

                print(traceback.format_exc())

            if not script_execution_success:

                await _create_fallback_react_app(sandbox)

            await _ensure_css_files(sandbox)
            await _fix_vite_css_processing(sandbox)
            await _ensure_tailwind_cdn_in_index_html(sandbox)

            await _async_sandbox_command(
                sandbox, "cd my-app && rm -rf node_modules/.vite", 10
            )
            await _async_sandbox_command(sandbox, "cd my-app && rm -rf .vite", 10)
            public_host = sandbox.get_host(port)
            await _write_vite_config(sandbox, public_host, port)
            final_url = await _start_dev_server(sandbox, port=port)
            if not final_url:
                final_url = await _start_preview_server(
                    sandbox, port_primary=port, port_fallback=4173
                )

            if not final_url:
                raise RuntimeError("Dev server not accessible after generation")

            ctx["sandbox_result"] = {
                "success": True,
                "url": final_url,
                "port": port,
                "sandbox_id": getattr(sandbox, "id", "unknown"),
                "message": "Application deployed successfully",
            }

        except Exception as e:
            import traceback

            print(traceback.format_exc())

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

    try:
        complete_state = {
            "e2b_script": None,
            "is_correction": False,
            "is_edit": False,
            "complete_files": {},
        }

        critical_files = [
            "src/App.jsx",
            "src/main.jsx",
            "src/index.css",
            "package.json",
            "index.html",
        ]

        try:
            # List all files in src directory
            src_files_result = await _async_sandbox_command(
                sandbox,
                "find my-app/src -name '*.jsx' -o -name '*.js' -o -name '*.css'",
                10,
            )
            if src_files_result and src_files_result.stdout:
                additional_files = [
                    f.strip() for f in src_files_result.stdout.split("\n") if f.strip()
                ]
                for file_path in additional_files:
                    if file_path not in critical_files:
                        critical_files.append(file_path.replace("my-app/", ""))
        except Exception as e:
            print(f"⚠️ Could not list additional files: {e}")

        for file_path in critical_files:
            try:
                full_path = f"my-app/{file_path}"
                content = await _async_sandbox_file_read(sandbox, full_path)
                if content:
                    complete_state["complete_files"][file_path] = content

            except Exception as e:
                print(f"   ⚠️ Could not capture {file_path}: {e}")

        script_lines = []
        script_lines.append("def create_react_app(sandbox):")
        script_lines.append('    """Recreate complete application from stored state"""')
        script_lines.append(
            "    print('Recreating complete application from stored state...')"
        )

        for file_path, content in complete_state["complete_files"].items():

            escaped_content = (
                content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            )
            script_lines.append(f"    # Recreate {file_path}")
            script_lines.append(
                f'    {file_path.replace("/", "_").replace(".", "_")}_content = """{escaped_content}"""'
            )
            script_lines.append(
                f'    sandbox.files.write("my-app/{file_path}", {file_path.replace("/", "_").replace(".", "_")}_content)'
            )
            script_lines.append(f'    print(f"✅ Recreated {file_path}")')

        script_lines.append(
            "    print('✅ Complete application recreated successfully')"
        )
        script_lines.append(
            "    return 'Complete application recreated from stored state'"
        )

        complete_script = "\n".join(script_lines)
        complete_state["e2b_script"] = complete_script

        return complete_state

    except Exception as e:

        return None


def _fix_tailwind_postcss_plugin(sandbox: Sandbox) -> bool:
    """No longer needed - Tailwind comes from CDN"""

    return True


async def _try_alternative_postcss_setup(sandbox: Sandbox) -> bool:
    """Try alternative PostCSS setup if the main one fails"""

    try:

        await _async_sandbox_command(
            sandbox, "cd my-app && mv postcss.config.fallback.js postcss.config.js", 5
        )

        commonjs_postcss = """module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        await _async_sandbox_file_write(
            sandbox, "my-app/postcss.config.cjs", commonjs_postcss
        )

        simple_postcss = """export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}"""
        await _async_sandbox_file_write(
            sandbox, "my-app/postcss.config.simple.js", simple_postcss
        )

        return True

    except Exception as e:

        return False


async def _fix_vite_css_processing(sandbox: Sandbox) -> bool:
    """Minimal Vite config - no PostCSS needed"""

    try:

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

        return True

    except Exception as e:

        return False


async def _validate_project_structure(sandbox: Sandbox) -> bool:
    """Validate that the project structure is intact."""

    critical_files = [
        "my-app/package.json",
        "my-app/src/main.jsx",
        "my-app/src/App.jsx",
        "my-app/src/index.css",
    ]

    for file_path in critical_files:
        try:
            content = await _async_sandbox_file_read(sandbox, file_path)
            if not content:

                return False
        except Exception as e:

            return False

    try:
        result = await _async_sandbox_command(sandbox, "cd my-app && npm --version", 10)
        if result.exit_code != 0:

            return False
    except Exception as e:

        return False

    return True


async def _validate_critical_files(sandbox: Sandbox) -> bool:
    """Validate that critical files contain valid content."""

    try:

        app_content = await _async_sandbox_file_read(sandbox, "my-app/src/App.jsx")
        if (
            not app_content
            or "function " not in app_content
            or "export default" not in app_content
        ):

            return False

        main_content = await _async_sandbox_file_read(sandbox, "my-app/src/main.jsx")
        if not main_content or "import App" not in main_content:

            return False

        package_content = await _async_sandbox_file_read(sandbox, "my-app/package.json")
        if not package_content or "dependencies" not in package_content:

            return False

        return True

    except Exception as e:

        return False


async def _backup_critical_files(sandbox: Sandbox) -> Dict[str, str]:
    """Backup critical files before making corrections."""

    backup_files = {}
    critical_files = [
        "my-app/src/App.jsx",
        "my-app/src/main.jsx",
        "my-app/src/index.css",
        "my-app/package.json",
    ]

    for file_path in critical_files:
        try:
            content = await _async_sandbox_file_read(sandbox, file_path)
            if content:
                backup_files[file_path] = content

        except Exception as e:
            print(f"   ⚠️ Could not backup {file_path}: {e}")

    return backup_files


async def _restore_from_backup(sandbox: Sandbox, backup_files: Dict[str, str]) -> bool:
    """Restore project from backup files."""

    try:
        for file_path, content in backup_files.items():
            try:
                await _async_sandbox_file_write(sandbox, file_path, content)

            except Exception as e:

                return False

        return True

    except Exception as e:

        return False


async def _validate_file_content(file_path: str, content: str) -> bool:
    """Validate file content before writing."""

    if not content or len(content.strip()) < 10:

        return False

    if file_path.endswith(".jsx") or file_path.endswith(".js"):
        if "import React" not in content and "React" in content:

            return False

        if "export default" not in content and "function " in content:

            return False

    elif file_path.endswith(".css"):
        if "@tailwind" not in content:

            return False

    return True


async def _get_existing_sandbox_only(ctx: Dict[str, Any]):
    """Get existing sandbox ONLY - never create new one during corrections."""
    session_id = ctx.get("session_id", "default")
    sandbox = _get_session_sandbox(session_id)

    if sandbox is None:
        return None

    try:

        test_result = await _async_sandbox_command(sandbox, "echo 'test'", 5)
        if test_result and test_result.stdout:
            sandbox_id = getattr(sandbox, "id", "unknown")

            return sandbox
    except Exception as e:
        print(f"⚠️ Sandbox health check failed: {e}")

    return None


async def _apply_edit_changes(correction_data: Dict[str, Any], session_id: str) -> bool:
    """Apply edit changes to the existing sandbox with robust validation and dependency installation."""
    sandbox = _get_session_sandbox(session_id)

    if not sandbox:

        return False

    try:

        if not await _validate_project_structure(sandbox):

            return False

        backup_files = await _backup_critical_files(sandbox)
        if not backup_files:
            print("⚠️ Could not backup critical files, proceeding with caution")

        all_new_content = []
        files_to_correct = correction_data.get("files_to_correct", [])
        new_files = correction_data.get("new_files", [])

        for file_correction in files_to_correct:
            content = file_correction.get("corrected_content", "")
            if content:
                all_new_content.append(content)

        for file_info in new_files:
            content = file_info.get("content", "")
            if content:
                all_new_content.append(content)

        if all_new_content:

            combined_content = "\n".join(all_new_content)

            try:
                installed_packages = await _detect_and_install_dependencies(
                    sandbox, combined_content
                )
                if installed_packages:

                    await asyncio.sleep(2)
                else:
                    print("ℹ️ No new dependencies detected in edited files")
            except Exception as e:
                print(f"⚠️ Warning: Could not install dependencies: {e}")

        for file_correction in files_to_correct:
            file_path = file_correction.get("path", "")
            corrected_content = file_correction.get("corrected_content", "")

            if file_path and corrected_content:

                full_path = (
                    f"my-app/{file_path}"
                    if not file_path.startswith("my-app/")
                    else file_path
                )

                try:

                    if not await _validate_file_content(file_path, corrected_content):

                        continue

                    await _async_sandbox_file_write(
                        sandbox, full_path, corrected_content
                    )

                    verify_content = await _async_sandbox_file_read(sandbox, full_path)
                    if verify_content == corrected_content:
                        print(f"   ✅ Verified: {file_path} updated successfully")
                    else:
                        print(
                            f"   ⚠️ Warning: {file_path} content may not have updated correctly"
                        )

                except Exception as e:

                    if backup_files and file_path in backup_files:
                        await _async_sandbox_file_write(
                            sandbox, full_path, backup_files[file_path]
                        )

                    return False

        for file_info in new_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")

            if file_path and content:

                full_path = (
                    f"my-app/{file_path}"
                    if not file_path.startswith("my-app/")
                    else file_path
                )

                try:
                    await _async_sandbox_file_write(sandbox, full_path, content)

                except Exception as e:

                    return False

        if not await _validate_project_structure(sandbox):

            if backup_files:
                await _restore_from_backup(sandbox, backup_files)

                return False
            else:

                return False

        if not await _validate_critical_files(sandbox):
            return False
        return True

    except Exception as e:

        if "backup_files" in locals() and backup_files:
            await _restore_from_backup(sandbox, backup_files)

        return False


def cleanup_session_sandbox(session_id: str):
    """Clean up sandbox for a specific session"""
    with _sandbox_lock:
        if session_id in _session_sandboxes:
            sandbox = _session_sandboxes[session_id]["sandbox"]
            try:
                sandbox.kill()

            except Exception as e:
                print(f"⚠️ Error cleaning up sandbox for session {session_id}: {e}")
            del _session_sandboxes[session_id]


def cleanup_all_sessions():
    """Clean up all session sandboxes"""
    with _sandbox_lock:
        for session_id in list(_session_sandboxes.keys()):
            cleanup_session_sandbox(session_id)
