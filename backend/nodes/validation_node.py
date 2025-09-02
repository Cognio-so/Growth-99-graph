# nodes/validation_node.py
import re
import ast
from typing import Dict, Any, List, Tuple
from pathlib import Path

def validate_generated_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive validation of generated code files.
    Now validates actual files from the sandbox instead of just the script.
    """
    print("--- Running Validation Node ---")
    
    ctx = state.get("context", {})
    sandbox_result = ctx.get("sandbox_result", {})
    
    # Check if sandbox deployment was successful
    if not sandbox_result.get("success"):
        print("❌ Sandbox deployment failed, no code to validate")
        ctx["validation_result"] = {
            "success": False,
            "errors": [{"type": "deployment_failure", "message": "Sandbox deployment failed"}],
            "error_type": "deployment_failure"
        }
        state["context"] = ctx
        return state
    
    print("🔍 Starting comprehensive code validation...")
    
    # Run validation on actual files from sandbox
    validation_errors: List[Dict[str, Any]] = []
    
    # Import the global sandbox to validate actual files
    try:
        from nodes.apply_to_Sandbox_node import _global_sandbox
        
        if _global_sandbox:
            print("📋 Validating actual files from sandbox...")
            
            # Validate App.jsx content
            try:
                app_content = _global_sandbox.files.read("my-app/src/App.jsx")
                if app_content:
                    jsx_errors = _validate_jsx_content(app_content)
                    validation_errors.extend(jsx_errors)
                    
                    component_errors = _validate_react_component_content(app_content)
                    validation_errors.extend(component_errors)
                else:
                    validation_errors.append({
                        "type": "missing_file",
                        "message": "App.jsx file not found",
                        "file": "src/App.jsx",
                        "severity": "critical"
                    })
            except Exception as e:
                print(f"⚠️ Could not read App.jsx: {e}")
                validation_errors.append({
                    "type": "file_access_error",
                    "message": f"Could not access App.jsx: {e}",
                    "file": "src/App.jsx",
                    "severity": "high"
                })
            
            # Validate CSS files
            try:
                css_files = ["my-app/src/App.css", "my-app/src/index.css"]
                for css_file in css_files:
                    try:
                        css_content = _global_sandbox.files.read(css_file)
                        if not css_content:
                            validation_errors.append({
                                "type": "missing_css",
                                "message": f"CSS file {css_file} is empty or missing",
                                "file": css_file.replace("my-app/", ""),
                                "severity": "medium"
                            })
                    except Exception:
                        validation_errors.append({
                            "type": "missing_css",
                            "message": f"CSS file {css_file} not found",
                            "file": css_file.replace("my-app/", ""),
                            "severity": "medium"
                        })
            except Exception as e:
                print(f"⚠️ Could not validate CSS files: {e}")

            # Validate ALL JSX files for JSX/structure issues
            try:
                jsx_files = _list_src_jsx_files(_global_sandbox)
                for rel in jsx_files:
                    try:
                        content = _global_sandbox.files.read(f"my-app/{rel}")
                        if content:
                            validation_errors.extend(_validate_jsx_content(content))
                            validation_errors.extend(_validate_react_component_content(content))
                    except Exception:
                        pass
            except Exception:
                pass
        
        else:
            print("⚠️ No global sandbox available, falling back to script validation")
            # Fallback to script validation
            gen_result = ctx.get("generation_result", {})
            generated_script = gen_result.get("e2b_script", "")
            
            if generated_script:
                python_errors = _validate_python_syntax(generated_script)
                validation_errors.extend(python_errors)
                
                jsx_errors = _validate_jsx_patterns(generated_script)
                validation_errors.extend(jsx_errors)

    except Exception as e:
        print(f"⚠️ Error during validation: {e}")
        validation_errors.append({
            "type": "validation_error",
            "message": f"Validation process failed: {e}",
            "file": "unknown",
            "severity": "high"
        })

    # NEW: Parse build errors from the running dev server log
    try:
        from nodes.apply_to_Sandbox_node import _global_sandbox as _gs
        if _gs:
            build_errors = _parse_build_errors_from_devlog(_gs)
            if build_errors:
                validation_errors.extend(build_errors)
    except Exception as _e:
        pass
    
    # Capture file content for targeted corrections
    if validation_errors:
        print(f"❌ Validation failed with {len(validation_errors)} errors:")
        for i, error in enumerate(validation_errors, 1):
            print(f"   {i}. {error['message']} (Type: {error['type']})")
        
        # Capture the actual generated files for correction
        file_content_for_correction = _capture_generated_files_for_correction(ctx)
        
        ctx["validation_result"] = {
            "success": False,
            "errors": validation_errors,
            "error_count": len(validation_errors),
            "requires_correction": True,
            "file_content_for_correction": file_content_for_correction
        }
    else:
        print("✅ All validation checks passed!")
        ctx["validation_result"] = {
            "success": True,
            "errors": [],
            "message": "Code validation successful"
        }
    
    state["context"] = ctx
    return state


def _validate_jsx_content(content: str) -> List[Dict[str, str]]:
    """Validate JSX content from actual file. Fixed false positive detection."""
    errors: List[Dict[str, str]] = []
    
    # More accurate check for unescaped quotes in className - FIXED
    # Only flag actual problematic patterns, not normal JSX
    problematic_patterns = [
        r'className="[^"]*\\"[^"]*"',  # className="text-\"red\"-500"
        r'className="[^"]*""[^"]*"',  # className="text-xl""extra"
    ]
    
    has_unescaped_quotes = False
    for pattern in problematic_patterns:
        if re.search(pattern, content):
            has_unescaped_quotes = True
            break
    
    # Additional check: look for common problematic patterns
    if 'className="' in content and '""' in content:
        has_unescaped_quotes = True
    
    if has_unescaped_quotes:
        errors.append({
            "type": "jsx_quotes",
            "message": "Unescaped quotes in JSX className attribute",
            "fix": "Escape quotes in className values or use single quotes",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for proper JSX syntax - brace matching
    if content.count("{") != content.count("}"):
        errors.append({
            "type": "jsx_braces",
            "message": "Mismatched curly braces in JSX",
            "fix": "Ensure equal number of opening and closing braces",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    return errors


def _validate_react_component_content(content: str) -> List[Dict[str, str]]:
    """Validate React component structure from actual file."""
    errors: List[Dict[str, str]] = []
    
    # Check for React import
    if "import React" not in content and "React" in content:
        errors.append({
            "type": "missing_import",
            "message": "React used but not imported",
            "fix": "Add: import React from 'react';",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for function definition
    if not re.search(r'function\s+\w+\s*\(|\w+\s*=\s*\(', content):
        errors.append({
            "type": "invalid_component",
            "message": "No valid React component function found",
            "fix": "Define component as: function ComponentName() { ... }",
            "file": "src/App.jsx",
            "severity": "critical"
        })
    
    # Check for export default
    if "function " in content and "export default" not in content:
        errors.append({
            "type": "missing_export",
            "message": "React component defined but missing 'export default'",
            "fix": "Add: export default ComponentName;",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    return errors


def _validate_python_syntax(script: str) -> List[Dict[str, str]]:
    """Validate Python syntax in the generated script."""
    errors: List[Dict[str, str]] = []
    try:
        # Try to parse the Python script
        ast.parse(script)
    except SyntaxError as e:
        errors.append({
            "type": "python_syntax",
            "message": f"Python syntax error: {e.msg} at line {e.lineno}",
            "line": e.lineno,
            "details": str(e)
        })
    except Exception as e:
        errors.append({
            "type": "python_parse",
            "message": f"Python parsing error: {str(e)}",
            "details": str(e)
        })
    return errors


def _validate_jsx_patterns(script: str) -> List[Dict[str, str]]:
    """Check for common JSX syntax errors that AI often makes."""
    errors: List[Dict[str, str]] = []
    
    # Check for incorrect style syntax
    if re.search(r'style=\s*{\s*[^{]', script):
        errors.append({
            "type": "jsx_style",
            "message": "Invalid JSX style syntax - style attributes should use double braces {{ }}",
            "pattern": "style={{ ... }}",
            "fix": "style={{ ... }}",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for unescaped quotes in JSX
    if re.search(r'className="[^"]*"[^"]*"', script):
        errors.append({
            "type": "jsx_quotes",
            "message": "Unescaped quotes in JSX className attribute",
            "pattern": 'className="value"extra"',
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for missing closing braces
    open_braces = script.count('{')
    close_braces = script.count('}')
    if open_braces != close_braces:
        errors.append({
            "type": "jsx_braces",
            "message": f"Mismatched JSX braces: {open_braces} opening, {close_braces} closing",
            "details": f"Difference: {open_braces - close_braces}",
            "file": "src/App.jsx",
            "severity": "critical"
        })
    
    return errors


def _validate_imports(script: str) -> List[Dict[str, str]]:
    """Enhanced import validation that detects external dependencies."""
    errors: List[Dict[str, str]] = []
    
    # Check if React components are used without import
    if "React" in script and "import React" not in script:
        errors.append({
            "type": "missing_import",
            "message": "React is used but not imported",
            "fix": "Add: import React from 'react';",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for external package imports that aren't installed
    external_package_patterns = [
        r'import\s+.*?\s+from\s+["\']([^"\'./][^"\']*)["\']',  # Named imports
        r'import\s+["\']([^"\'./][^"\']*)["\']'  # Side effect imports
    ]
    
    # Common packages that shouldn't be used (not installed by default)
    forbidden_packages = [
        'lucide-react', 'react-icons', 'heroicons', 'feather-icons',
        'styled-components', 'emotion', 'framer-motion', 'react-spring',
        'lodash', 'moment', 'date-fns', 'axios', 'fetch'
    ]
    
    for pattern in external_package_patterns:
        imports = re.findall(pattern, script)
        for imported_package in imports:
            if imported_package in forbidden_packages:
                errors.append({
                    "type": "forbidden_dependency",
                    "message": f"External package '{imported_package}' is not installed",
                    "package": imported_package,
                    "fix": f"Replace '{imported_package}' with built-in React or remove the import",
                    "file": "src/components/[component].jsx",
                    "severity": "critical"
                })
    
    # Check for CSS imports without file creation
    css_imports = re.findall(r'import\s+["\']([^"\']+\.css)["\']', script)
    for css_file in css_imports:
        if "sandbox.files.write" not in script or css_file not in script:
            errors.append({
                "type": "missing_css_file",
                "message": f"CSS file '{css_file}' is imported but not created",
                "file": css_file,
                "severity": "high"
            })
    
    return errors


def _validate_tailwind_usage(script: str) -> List[Dict[str, str]]:
    """Check for Tailwind CSS configuration issues."""
    errors: List[Dict[str, str]] = []
    
    # Check if Tailwind classes are used but config is missing
    tailwind_patterns = [
        r'className="[^"]*(?:bg-|text-|p-|m-|flex|grid)',
        r'className=\{[^}]*(?:bg-|text-|p-|m-|flex|grid)'
    ]
    
    has_tailwind_classes = any(re.search(pattern, script) for pattern in tailwind_patterns)
    has_tailwind_config = "tailwind.config.js" in script
    
    if has_tailwind_classes and not has_tailwind_config:
        errors.append({
            "type": "missing_tailwind_config",
            "message": "Tailwind CSS classes used but tailwind.config.js not configured",
            "fix": "Ensure tailwind.config.js is properly set up",
            "file": "tailwind.config.js",
            "severity": "critical"
        })
    
    return errors


def _validate_component_structure(script: str) -> List[Dict[str, str]]:
    """Check for proper React component structure."""
    errors: List[Dict[str, str]] = []
    
    # Check for export default
    if "function " in script and "export default" not in script:
        errors.append({
            "type": "missing_export",
            "message": "React component defined but missing 'export default'",
            "file": "src/App.jsx",
            "severity": "high"
        })
    
    # Check for proper function declaration
    if not re.search(r'function\s+\w+\s*\(|\w+\s*=\s*\(', script):
        errors.append({
            "type": "invalid_component",
            "message": "No valid React component function found",
            "fix": "Define component as: function ComponentName() { ... }",
            "file": "src/App.jsx",
            "severity": "critical"
        })
    
    return errors


def _validate_server_startup(sandbox) -> List[Dict[str, str]]:
    """Enhanced validation that checks for dependency errors and build failures."""
    errors: List[Dict[str, str]] = []
    
    try:
        print("🔍 Validating server startup and dependencies...")
        
        # Start the dev server and capture output
        result = sandbox.commands.run("cd my-app && npm run dev", timeout=15)
        
        # Check for dependency errors
        output_text = result.stdout + result.stderr if result.stderr else result.stdout
        
        # Check for common dependency import errors
        dependency_error_patterns = [
            (r'Failed to resolve import "([^"]+)"', "missing_dependency"),
            (r"Cannot resolve module '([^']+)'", "missing_dependency"),
            (r'Module not found: Error: Can\'t resolve \'([^\']+)\'', "missing_dependency"),
            (r'Error: Cannot find module \'([^\']+)\'', "missing_dependency")
        ]
        
        for pattern, error_type in dependency_error_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            for missing_package in matches:
                errors.append({
                    "type": error_type,
                    "message": f"Missing dependency: {missing_package}",
                    "package": missing_package,
                    "fix": f"Remove import of '{missing_package}' or replace with built-in alternatives",
                    "file": "src/components/[component].jsx",
                    "severity": "critical"
                })
                print(f"   ❌ Missing dependency detected: {missing_package}")
        
        # Check for build/compilation errors
        build_error_patterns = [
            (r'SyntaxError: (.+)', "syntax_error"),
            (r'TypeError: (.+)', "type_error"),
            (r'ReferenceError: (.+)', "reference_error"),
            (r'Error: (.+)', "general_error")
        ]
        
        for pattern, error_type in build_error_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            for error_msg in matches:
                if "Failed to resolve import" not in error_msg:  # Already handled above
                    errors.append({
                        "type": error_type,
                        "message": f"Build error: {error_msg}",
                        "details": error_msg,
                        "severity": "high"
                    })
        
        # Check if server started successfully
        success_indicators = [
            "Local:",
            "ready in",
            "VITE",
            "localhost:",
            "Network:"
        ]
        
        server_started = any(indicator in output_text for indicator in success_indicators)
        
        if not server_started and not errors:
            errors.append({
                "type": "server_startup_failed",
                "message": "Development server failed to start",
                "details": output_text,
                "severity": "critical"
            })
        
        if server_started and not errors:
            print("   ✅ Development server started successfully")
        
    except Exception as e:
        print(f"   ⚠️ Server validation error: {e}")
        errors.append({
            "type": "validation_error",
            "message": f"Could not validate server startup: {e}",
            "severity": "high"
        })
    
    return errors


def _list_src_jsx_files(sandbox) -> List[str]:
    """List all JSX files under src/ to validate each file, not just App.jsx."""
    try:
        res = sandbox.commands.run("bash -lc \"ls -1 my-app/src/**/*.jsx 2>/dev/null || true\"")
        lines = (res.stdout or "").splitlines()
        files = [line.strip().replace("my-app/", "") for line in lines if line.strip()]
        if "src/App.jsx" not in files:
            files.append("src/App.jsx")
        return files
    except Exception:
        return ["src/App.jsx"]


def _parse_build_errors_from_devlog(sandbox) -> List[Dict[str, Any]]:
    """Parse Vite/esbuild errors from dev.log into structured validation errors."""
    errors: List[Dict[str, Any]] = []
    try:
        log = sandbox.files.read("my-app/dev.log")
        if not log:
            return errors
    except Exception:
        return errors

    # 1) esbuild exact file:line:col errors
    for m in re.finditer(r"my-app/(src/[^\s:]+):(\d+):(\d+):\s+ERROR:\s+(.+)", log):
        file_path, line, col, msg = m.groups()
        errors.append({
            "type": "build_error",
            "message": msg.strip(),
            "file": file_path,
            "line": int(line),
            "column": int(col),
            "severity": "critical"
        })

    # 2) Correlate Vite "Failed to resolve import" with the previous file context
    # We walk line-by-line to pair:
    #   /home/user/my-app/src/App.jsx:4:25
    #   [plugin:vite:import-analysis] Failed to resolve import "./components/IntroSection"
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
                "severity": "critical"
            }

            # Compute the missing component file path if it's a relative import
            if pkg.startswith("./") or pkg.startswith("../") or pkg.startswith("components/"):
                # Normalize to a src-relative .jsx file path
                base_dir = "/".join(src_file.split("/")[:-1])
                rel = pkg
                if not rel.endswith(".jsx") and not rel.endswith(".js"):
                    rel = f"{rel}.jsx"
                # Join base_dir + rel (POSIX-safe join)
                parts = (base_dir + "/" + rel).split("/")
                norm = []
                for p in parts:
                    if p == ".." and norm:
                        norm.pop()
                    elif p != ".":
                        norm.append(p)
                missing_path = "/".join(norm)
                # Ensure it stays under src/
                if not missing_path.startswith("src/") and "src/" in missing_path:
                    missing_path = missing_path[missing_path.index("src/"):]
                err["missing_component_path"] = missing_path

            errors.append(err)

    # 3) Generic transform failed banner
    if "[plugin:vite:esbuild] Transform failed" in log and not errors:
        errors.append({
            "type": "build_error",
            "message": "Vite/esbuild transform failed (see dev.log for details)",
            "file": "unknown",
            "severity": "critical"
        })

    # 4) Common syntax/build hints
    if re.search(r"Unterminated string|Unexpected token", log, re.IGNORECASE):
        errors.append({
            "type": "syntax_error",
            "message": "Build failed: string/JSX token issue (check quotes and JSX braces)",
            "file": "unknown",
            "severity": "high"
        })

    if re.search(r"is not defined", log):
        undef = re.search(r"\'([^']+)\' is not defined", log)
        symbol = undef.group(1) if undef else "variable"
        errors.append({
            "type": "reference_error",
            "message": f"ReferenceError: {symbol} is not defined",
            "file": "unknown",
            "severity": "high"
        })

    if "Expected \"}\"" in log and "style" in log:
        errors.append({
            "type": "jsx_style",
            "message": "Invalid JSX style syntax detected in build output. Use style={{ ... }} and escape quotes in data URLs.",
            "file": "unknown",
            "severity": "high"
        })

    return errors

def _capture_generated_files_for_correction(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Capture the actual generated files for targeted correction."""
    try:
        # Import the global sandbox reference
        from nodes.apply_to_Sandbox_node import _global_sandbox
        
        # Collect target files from validation errors
        val = ctx.get("validation_result", {}) or {}
        err_list = val.get("errors", []) or []
        dynamic_targets = set()
        missing_components = set()

        for e in err_list:
            if isinstance(e, dict):
                fp = e.get("file")
                if isinstance(fp, str) and fp.startswith("src/"):
                    dynamic_targets.add(fp)
                mp = e.get("missing_component_path") or e.get("missing_file")
                if isinstance(mp, str) and mp.startswith("src/"):
                    missing_components.add(mp)

        # Default core files
        default_targets = {"src/App.jsx", "src/index.css"}
        target_files = sorted(default_targets.union(dynamic_targets).union(missing_components))

        if _global_sandbox:
            print("📁 Capturing files from persistent sandbox for correction...")
            
            files_content: Dict[str, str] = {}
            for file_path in target_files:
                try:
                    full_path = f"my-app/{file_path}" if not file_path.startswith("my-app/") else file_path
                    content = _global_sandbox.files.read(full_path)
                    if content:
                        files_content[file_path] = content
                        print(f"   ✅ Captured: {file_path}")
                    else:
                        # Mark missing files explicitly (to be created by correction)
                        if file_path not in files_content:
                            files_content[file_path] = ""
                            print(f"   ❓ Will create missing file: {file_path}")
                except Exception:
                    # If read fails, mark as missing to be created
                    files_content[file_path] = ""
                    print(f"   ❓ Will create missing file: {file_path}")
            
            return {
                "files_content": files_content,
                "target_files": list(files_content.keys()),
                "missing_components": list(missing_components),
                "sandbox_available": True
            }
        
        # Fallback: use the generated script
        generation_result = ctx.get("generation_result", {})
        generated_script = generation_result.get("e2b_script", "")
        
        return {
            "generated_script": generated_script,
            "target_files": list(target_files) or ["src/App.jsx"],
            "missing_components": list(missing_components),
            "sandbox_available": False
        }
        
    except Exception as e:
        print(f"⚠️ Could not capture files for correction: {e}")
        return {}

def route_after_analysis(state: Dict[str, Any]) -> str:
    """Route after code analysis - check if we need full regeneration after repeated failures."""
    ctx = state.get("context", {})
    attempts = ctx.get("correction_attempts", 0)
    
    # After 3 failed validation attempts, switch to regenerate mode
    if attempts >= 3:
        print(f"🔄 Too many correction attempts ({attempts}) - switching to REGENERATE mode")
        # Force full regeneration on next generator run
        ctx["force_regeneration"] = True
        # Emulate "Regenerate" button -> make schema_extraction pick a random schema
        meta = state.get("metadata") or {}
        meta["regenerate"] = True
        state["metadata"] = meta
        # Reset attempts to avoid immediate re-trigger loops
        ctx["correction_attempts"] = 0
        return "generator"
    
    print(f"🔄 Sending to generator for correction (attempt #{attempts})")
    return "generator"