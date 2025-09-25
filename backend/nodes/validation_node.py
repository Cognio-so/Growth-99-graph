# nodes/validation_node.py
import re
import ast
from typing import Dict, Any, List, Tuple
from pathlib import Path

from graph_types import GraphState


async def validate_generated_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive validation of generated code files.
    Now validates actual files from the sandbox instead of just the script.
    """

    ctx = state.get("context", {})
    sandbox_result = ctx.get("sandbox_result", {})

    if not sandbox_result.get("success"):

        ctx["validation_result"] = {
            "success": False,
            "errors": [
                {"type": "deployment_failure", "message": "Sandbox deployment failed"}
            ],
            "error_type": "deployment_failure",
        }
        state["context"] = ctx
        return state

    validation_errors: List[Dict[str, Any]] = []

    try:

        from nodes.apply_to_Sandbox_node import _get_session_sandbox

        session_id = state.get("session_id", "default")
        sandbox = _get_session_sandbox(session_id)
        if sandbox:

            try:
                app_content = sandbox.files.read("my-app/src/App.jsx")
                if app_content:
                    jsx_errors = await _validate_jsx_content(app_content)
                    validation_errors.extend(jsx_errors)

                    component_errors = await _validate_react_component_content(
                        app_content
                    )
                    validation_errors.extend(component_errors)
                else:
                    validation_errors.append(
                        {
                            "type": "missing_file",
                            "message": "App.jsx file not found",
                            "file": "src/App.jsx",
                            "severity": "critical",
                        }
                    )
            except Exception as e:

                validation_errors.append(
                    {
                        "type": "file_access_error",
                        "message": f"Could not access App.jsx: {e}",
                        "file": "src/App.jsx",
                        "severity": "high",
                    }
                )

            try:
                css_files = ["my-app/src/App.css", "my-app/src/index.css"]
                for css_file in css_files:
                    try:
                        css_content = sandbox.files.read(css_file)
                        if not css_content:
                            validation_errors.append(
                                {
                                    "type": "missing_css",
                                    "message": f"CSS file {css_file} is empty or missing",
                                    "file": css_file.replace("my-app/", ""),
                                    "severity": "medium",
                                }
                            )
                    except Exception:
                        validation_errors.append(
                            {
                                "type": "missing_css",
                                "message": f"CSS file {css_file} not found",
                                "file": css_file.replace("my-app/", ""),
                                "severity": "medium",
                            }
                        )
            except Exception as e:
                print(f"⚠️ Could not validate CSS files: {e}")

            try:
                jsx_files = await _list_src_jsx_files(sandbox)
                for rel in jsx_files:
                    try:
                        content = sandbox.files.read(f"my-app/{rel}")
                        if content:
                            validation_errors.extend(
                                await _validate_jsx_content(content)
                            )
                            validation_errors.extend(
                                await _validate_react_component_content(content)
                            )
                    except Exception:
                        pass
            except Exception:
                pass

        else:

            gen_result = ctx.get("generation_result", {})
            generated_script = gen_result.get("e2b_script", "")

            if generated_script:
                python_errors = await _validate_python_syntax(generated_script)
                validation_errors.extend(python_errors)

                jsx_errors = await _validate_jsx_patterns(generated_script)
                validation_errors.extend(jsx_errors)

    except Exception as e:

        validation_errors.append(
            {
                "type": "validation_error",
                "message": f"Validation process failed: {e}",
                "file": "unknown",
                "severity": "high",
            }
        )

    try:
        from nodes.apply_to_Sandbox_node import _get_session_sandbox

        session_id = state.get("session_id", "default")
        sandbox = _get_session_sandbox(session_id)

        if sandbox:
            build_errors = await _parse_build_errors_from_devlog(sandbox)
            if build_errors:
                validation_errors.extend(build_errors)
    except Exception as _e:
        pass

    if validation_errors:

        for i, error in enumerate(validation_errors, 1):
            print(f"   {i}. {error['message']} (Type: {error['type']})")

        file_content_for_correction = await _capture_generated_files_for_correction(
            state, ctx
        )

        ctx["validation_result"] = {
            "success": False,
            "errors": validation_errors,
            "error_count": len(validation_errors),
            "requires_correction": True,
            "file_content_for_correction": file_content_for_correction,
        }
    else:

        ctx["validation_result"] = {
            "success": True,
            "errors": [],
            "message": "Code validation successful",
        }

    state["context"] = ctx
    return state


async def _validate_jsx_content(content: str) -> List[Dict[str, str]]:
    """Validate JSX content from actual file. SIMPLIFIED - removed problematic checks."""
    errors: List[Dict[str, str]] = []

    if content.count("{") != content.count("}"):
        errors.append(
            {
                "type": "jsx_braces",
                "message": "Mismatched curly braces in JSX",
                "fix": "Ensure equal number of opening and closing braces",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    return errors


async def _validate_react_component_content(content: str) -> List[Dict[str, str]]:
    """Validate React component structure from actual file."""
    errors: List[Dict[str, str]] = []

    if "import React" not in content and "React" in content:
        errors.append(
            {
                "type": "missing_import",
                "message": "React used but not imported",
                "fix": "Add: import React from 'react';",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    if not re.search(r"function\s+\w+\s*\(|\w+\s*=\s*\(", content):
        errors.append(
            {
                "type": "invalid_component",
                "message": "No valid React component function found",
                "fix": "Define component as: function ComponentName() { ... }",
                "file": "src/App.jsx",
                "severity": "critical",
            }
        )

    if "function " in content and "export default" not in content:
        errors.append(
            {
                "type": "missing_export",
                "message": "React component defined but missing 'export default'",
                "fix": "Add: export default ComponentName;",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    return errors


async def _validate_python_syntax(script: str) -> List[Dict[str, str]]:
    """Validate Python syntax in the generated script."""
    errors: List[Dict[str, str]] = []
    try:
        # Try to parse the Python script
        ast.parse(script)
    except SyntaxError as e:
        errors.append(
            {
                "type": "python_syntax",
                "message": f"Python syntax error: {e.msg} at line {e.lineno}",
                "line": e.lineno,
                "details": str(e),
            }
        )
    except Exception as e:
        errors.append(
            {
                "type": "python_parse",
                "message": f"Python parsing error: {str(e)}",
                "details": str(e),
            }
        )
    return errors


async def _validate_jsx_patterns(script: str) -> List[Dict[str, str]]:
    """Check for common JSX syntax errors that AI often makes."""
    errors: List[Dict[str, str]] = []

    if re.search(r"style=\s*{\s*[^{]", script):
        errors.append(
            {
                "type": "jsx_style",
                "message": "Invalid JSX style syntax - style attributes should use double braces {{ }}",
                "pattern": "style={{ ... }}",
                "fix": "style={{ ... }}",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    open_braces = script.count("{")
    close_braces = script.count("}")
    if open_braces != close_braces:
        errors.append(
            {
                "type": "jsx_braces",
                "message": f"Mismatched JSX braces: {open_braces} opening, {close_braces} closing",
                "details": f"Difference: {open_braces - close_braces}",
                "file": "src/App.jsx",
                "severity": "critical",
            }
        )

    return errors


def _validate_imports(script: str) -> List[Dict[str, str]]:
    """Enhanced import validation that detects external dependencies."""
    errors: List[Dict[str, str]] = []

    if "React" in script and "import React" not in script:
        errors.append(
            {
                "type": "missing_import",
                "message": "React is used but not imported",
                "fix": "Add: import React from 'react';",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    external_package_patterns = [
        r'import\s+.*?\s+from\s+["\']([^"\'./][^"\']*)["\']',  # Named imports
        r'import\s+["\']([^"\'./][^"\']*)["\']',  # Side effect imports
    ]

    forbidden_packages = []

    for pattern in external_package_patterns:
        imports = re.findall(pattern, script)
        for imported_package in imports:
            if imported_package in forbidden_packages:
                errors.append(
                    {
                        "type": "forbidden_dependency",
                        "message": f"External package '{imported_package}' is not installed",
                        "package": imported_package,
                        "fix": f"Replace '{imported_package}' with built-in React or remove the import",
                        "file": "src/components/[component].jsx",
                        "severity": "critical",
                    }
                )

    css_imports = re.findall(r'import\s+["\']([^"\']+\.css)["\']', script)
    for css_file in css_imports:
        if "sandbox.files.write" not in script or css_file not in script:
            errors.append(
                {
                    "type": "missing_css_file",
                    "message": f"CSS file '{css_file}' is imported but not created",
                    "file": css_file,
                    "severity": "high",
                }
            )

    return errors


def _validate_tailwind_usage(script: str) -> List[Dict[str, str]]:
    """Check for Tailwind CSS configuration issues."""
    errors: List[Dict[str, str]] = []

    tailwind_patterns = [
        r'className="[^"]*(?:bg-|text-|p-|m-|flex|grid)',
        r"className=\{[^}]*(?:bg-|text-|p-|m-|flex|grid)",
    ]

    has_tailwind_classes = any(
        re.search(pattern, script) for pattern in tailwind_patterns
    )
    has_tailwind_config = "tailwind.config.js" in script

    if has_tailwind_classes and not has_tailwind_config:
        errors.append(
            {
                "type": "missing_tailwind_config",
                "message": "Tailwind CSS classes used but tailwind.config.js not configured",
                "fix": "Ensure tailwind.config.js is properly set up",
                "file": "tailwind.config.js",
                "severity": "critical",
            }
        )

    return errors


def _validate_component_structure(script: str) -> List[Dict[str, str]]:
    """Check for proper React component structure."""
    errors: List[Dict[str, str]] = []

    if "function " in script and "export default" not in script:
        errors.append(
            {
                "type": "missing_export",
                "message": "React component defined but missing 'export default'",
                "file": "src/App.jsx",
                "severity": "high",
            }
        )

    if not re.search(r"function\s+\w+\s*\(|\w+\s*=\s*\(", script):
        errors.append(
            {
                "type": "invalid_component",
                "message": "No valid React component function found",
                "fix": "Define component as: function ComponentName() { ... }",
                "file": "src/App.jsx",
                "severity": "critical",
            }
        )

    return errors


def _validate_server_startup(sandbox) -> List[Dict[str, str]]:
    """Enhanced validation that checks for dependency errors and build failures."""
    errors: List[Dict[str, str]] = []

    try:

        result = sandbox.commands.run("cd my-app && npm run dev", timeout=15)

        output_text = result.stdout + result.stderr if result.stderr else result.stdout

        dependency_error_patterns = [
            (r'Failed to resolve import "([^"]+)"', "missing_dependency"),
            (r"Cannot resolve module '([^']+)'", "missing_dependency"),
            (
                r"Module not found: Error: Can\'t resolve \'([^\']+)\'",
                "missing_dependency",
            ),
            (r"Error: Cannot find module \'([^\']+)\'", "missing_dependency"),
        ]

        for pattern, error_type in dependency_error_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            for missing_package in matches:
                errors.append(
                    {
                        "type": error_type,
                        "message": f"Missing dependency: {missing_package}",
                        "package": missing_package,
                        "fix": f"Remove import of '{missing_package}' or replace with built-in alternatives",
                        "file": "src/components/[component].jsx",
                        "severity": "critical",
                    }
                )

        build_error_patterns = [
            (r"SyntaxError: (.+)", "syntax_error"),
            (r"TypeError: (.+)", "type_error"),
            (r"ReferenceError: (.+)", "reference_error"),
            (r"Error: (.+)", "general_error"),
        ]

        for pattern, error_type in build_error_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            for error_msg in matches:
                if "Failed to resolve import" not in error_msg:  # Already handled above
                    errors.append(
                        {
                            "type": error_type,
                            "message": f"Build error: {error_msg}",
                            "details": error_msg,
                            "severity": "high",
                        }
                    )

        success_indicators = ["Local:", "ready in", "VITE", "localhost:", "Network:"]

        server_started = any(
            indicator in output_text for indicator in success_indicators
        )

        if not server_started and not errors:
            errors.append(
                {
                    "type": "server_startup_failed",
                    "message": "Development server failed to start",
                    "details": output_text,
                    "severity": "critical",
                }
            )

        if server_started and not errors:
            print("   ✅ Development server started successfully")

    except Exception as e:

        errors.append(
            {
                "type": "validation_error",
                "message": f"Could not validate server startup: {e}",
                "severity": "high",
            }
        )

    return errors


async def _list_src_jsx_files(sandbox) -> List[str]:
    """List all JSX files under src/ to validate each file, not just App.jsx."""
    try:
        res = sandbox.commands.run(
            'bash -lc "ls -1 my-app/src/**/*.jsx 2>/dev/null || true"'
        )
        lines = (res.stdout or "").splitlines()
        files = [line.strip().replace("my-app/", "") for line in lines if line.strip()]
        if "src/App.jsx" not in files:
            files.append("src/App.jsx")
        return files
    except Exception:
        return ["src/App.jsx"]


async def _parse_build_errors_from_devlog(sandbox) -> List[Dict[str, Any]]:
    """Parse Vite/esbuild errors from dev.log into structured validation errors."""
    errors: List[Dict[str, Any]] = []
    try:
        log = sandbox.files.read("my-app/dev.log")
        if not log:
            return errors
    except Exception:
        return errors

    for m in re.finditer(r"my-app/(src/[^\s:]+):(\d+):(\d+):\s+ERROR:\s+(.+)", log):
        file_path, line, col, msg = m.groups()
        errors.append(
            {
                "type": "build_error",
                "message": msg.strip(),
                "file": file_path,
                "line": int(line),
                "column": int(col),
                "severity": "critical",
            }
        )

    last_src_ctx = None
    for line in log.splitlines():
        ctx = re.search(r"my-app/(src/[^\s:]+):(\d+):(\d+)", line)
        if ctx:
            last_src_ctx = {
                "file": ctx.group(1),
                "line": int(ctx.group(2)),
                "column": int(ctx.group(3)),
            }
            continue

        m = re.search(r'Failed to resolve import\s+"([^"]+)"', line)
        if m:
            pkg = m.group(1)
            src_file = (last_src_ctx or {}).get("file", "src/App.jsx")
            err = {
                "type": "missing_import",
                "message": f'Failed to resolve import "{pkg}"',
                "file": src_file,
                "package": pkg,
                "severity": "critical",
            }

            if (
                pkg.startswith("./")
                or pkg.startswith("../")
                or pkg.startswith("components/")
            ):

                base_dir = "/".join(src_file.split("/")[:-1])
                rel = pkg
                if not rel.endswith(".jsx") and not rel.endswith(".js"):
                    rel = f"{rel}.jsx"

                parts = (base_dir + "/" + rel).split("/")
                norm = []
                for p in parts:
                    if p == ".." and norm:
                        norm.pop()
                    elif p != ".":
                        norm.append(p)
                missing_path = "/".join(norm)

                if not missing_path.startswith("src/") and "src/" in missing_path:
                    missing_path = missing_path[missing_path.index("src/") :]
                err["missing_component_path"] = missing_path

            errors.append(err)

    if "[plugin:vite:esbuild] Transform failed" in log and not errors:
        errors.append(
            {
                "type": "build_error",
                "message": "Vite/esbuild transform failed (see dev.log for details)",
                "file": "unknown",
                "severity": "critical",
            }
        )

    if re.search(r"Unterminated string|Unexpected token", log, re.IGNORECASE):
        errors.append(
            {
                "type": "syntax_error",
                "message": "Build failed: string/JSX token issue (check quotes and JSX braces)",
                "file": "unknown",
                "severity": "high",
            }
        )

    if re.search(r"is not defined", log):
        undef = re.search(r"\'([^']+)\' is not defined", log)
        symbol = undef.group(1) if undef else "variable"
        errors.append(
            {
                "type": "reference_error",
                "message": f"ReferenceError: {symbol} is not defined",
                "file": "unknown",
                "severity": "high",
            }
        )

    if 'Expected "}"' in log and "style" in log:
        errors.append(
            {
                "type": "jsx_style",
                "message": "Invalid JSX style syntax detected in build output. Use style={{ ... }} and escape quotes in data URLs.",
                "file": "unknown",
                "severity": "high",
            }
        )

    return errors


async def _capture_generated_files_for_correction(
    state: GraphState, ctx: Dict[str, Any]
) -> Dict[str, Any]:
    """Capture ALL generated files for comprehensive correction."""
    try:
        from nodes.apply_to_Sandbox_node import _get_session_sandbox

        session_id = state.get("session_id", "default")
        sandbox = _get_session_sandbox(session_id)
        if sandbox:

            files_content: Dict[str, str] = {}

            critical_files = ["src/App.jsx", "src/main.jsx", "src/index.css"]

            for file_path in critical_files:
                try:
                    full_path = f"my-app/{file_path}"
                    content = sandbox.files.read(full_path)
                    if content:
                        files_content[file_path] = content
                except Exception:
                    files_content[file_path] = ""

            try:
                ls_result = sandbox.commands.run(
                    "find my-app/src/components -name '*.jsx' -o -name '*.js'",
                    timeout=10,
                )
                if ls_result.stdout:
                    component_files = ls_result.stdout.strip().split("\n")
                    for file_path in component_files:
                        if file_path and "my-app/" in file_path:
                            relative_path = file_path.replace("my-app/", "")
                            try:
                                content = sandbox.files.read(file_path)
                                if content:
                                    files_content[relative_path] = content

                            except Exception:
                                print(f"   ⚠️ Could not capture: {relative_path}")
            except Exception:
                print("   ⚠️ Could not scan components directory")

            config_files = [
                "vite.config.js",
                "tailwind.config.js",
                "postcss.config.js",
                "index.html",
            ]

            for file_path in config_files:
                try:
                    full_path = f"my-app/{file_path}"
                    content = sandbox.files.read(full_path)
                    if content:
                        files_content[file_path] = content

                except Exception:
                    print(f"   ⚠️ Could not capture config: {file_path}")

            # CAPTURE PACKAGE.JSON (CRITICAL)
            try:
                package_content = sandbox.files.read("my-app/package.json")
                if package_content:
                    files_content["package.json"] = package_content

                else:
                    files_content["package.json"] = ""

            except Exception:
                files_content["package.json"] = ""

            return {
                "files_content": files_content,
                "target_files": list(files_content.keys()),
                "sandbox_available": True,
            }

    except Exception as e:

        return {}


async def route_after_validation_local(state: Dict[str, Any]) -> str:
    ctx = state.get("context", {})
    vr = ctx.get("validation_result", {})

    if vr.get("success"):
        ctx["correction_attempts"] = 0
        ctx["total_attempts"] = 0  # Reset total counter
        return "output"

    attempts = int(ctx.get("correction_attempts", 0)) + 1
    total_attempts = int(ctx.get("total_attempts", 0)) + 1
    ctx["correction_attempts"] = attempts
    ctx["total_attempts"] = total_attempts

    if vr.get("switch_to_schema"):

        ctx["correction_attempts"] = 0
        return "schema_extraction"

    if attempts <= 2:

        return "code_analysis"
    elif total_attempts >= 5:

        return "output"
    else:

        return "schema_extraction"
