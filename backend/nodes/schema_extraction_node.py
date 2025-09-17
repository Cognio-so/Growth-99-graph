# nodes/schema_extraction_node.py
from typing import Dict, Any, Optional
import json, re, csv, random
from pathlib import Path

# Schema file paths
SCHEMA_CSV_PATH = Path(__file__).parent.parent / "schema.csv"
SCHEMA2_CSV_PATH = Path(__file__).parent.parent / "schema2.csv"  # Medspa/Fashion & Beauty
SCHEMA3_CSV_PATH = Path(__file__).parent.parent / "schema3.csv"  # Dental & Medical
REGENERATION_COUNTER_FILE = Path(__file__).parent.parent / "regeneration_counter.json"

# Maximum uses of schema2.csv before falling back to schema.csv
MAX_SCHEMA2_USES = 7

# These are used ONLY if the CSV file is not found or is empty.
DEFAULT_ROWS = [
    {"name": "UserProfile", "json_schema": json.dumps({
        "title":"UserProfile","type":"object",
        "properties":{"id":{"type":"string"},"name":{"type":"string"},"email":{"type":"string","format":"email"}},
        "required":["id","name","email"]
    })},
    {"name": "Product", "json_schema": json.dumps({
        "title":"Product","type":"object",
        "properties":{"sku":{"type":"string"},"title":{"type":"string"},"price":{"type":"number"}},
        "required":["sku","title"]
    })},
]

def _get_regeneration_count(session_id: str = None) -> int:
    """Get the current regeneration count from persistent storage for a specific session."""
    try:
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)
                # If no session_id provided, use legacy global counter
                if not session_id:
                    return data.get("count", 0)
                # Return session-specific counter, defaulting to 0 for new sessions
                return data.get("sessions", {}).get(session_id, 0)
    except Exception as e:
        print(f"⚠️ Error reading regeneration counter: {e}")
    return 0

def _increment_regeneration_count(session_id: str = None) -> int:
    """Increment and save the regeneration count for a specific session."""
    try:
        # Load existing data
        data = {}
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)
        
        # Initialize sessions dict if it doesn't exist
        if "sessions" not in data:
            data["sessions"] = {}
        
        # Get current count for this session
        current_count = data["sessions"].get(session_id, 0) if session_id else data.get("count", 0)
        new_count = current_count + 1
        
        # Update the appropriate counter
        if session_id:
            data["sessions"][session_id] = new_count
            print(f"📊 Regeneration count for session {session_id}: {new_count}")
        else:
            # Legacy support for global counter
            data["count"] = new_count
            print(f"📊 Global regeneration count: {new_count}")
        
        # Save updated data
        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump(data, f)
        
        return new_count
    except Exception as e:
        print(f"⚠️ Error updating regeneration counter: {e}")
        return 0

def _reset_regeneration_count(session_id: str = None):
    """Reset regeneration count for a specific session (for testing or manual reset)."""
    try:
        # Load existing data
        data = {}
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)
        
        # Initialize sessions dict if it doesn't exist
        if "sessions" not in data:
            data["sessions"] = {}
        
        # Reset the appropriate counter
        if session_id:
            data["sessions"][session_id] = 0
            print(f"🔄 Regeneration counter reset to 0 for session {session_id}")
        else:
            # Legacy support for global counter
            data["count"] = 0
            print("🔄 Global regeneration counter reset to 0")
        
        # Save updated data
        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"⚠️ Error resetting regeneration counter: {e}")

def _load_schemas_from_csv(csv_path: Path) -> list[dict]:
    """Loads all valid schemas from the specified CSV file."""
    if not csv_path.exists():
        print(f"Schema CSV not found at '{csv_path}'.")
        return []

    rows = []
    try:
        with csv_path.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both "json_schema" and "JSON SCHEMA" column names
                json_schema = row.get("json_schema") or row.get("JSON SCHEMA")
                name = row.get("name") or row.get("S.No", "Unknown")
                
                # Ensure the required columns exist and are not empty
                if name and json_schema:
                    rows.append({"name": name, "json_schema": json_schema})
        
        print(f"📋 Loaded {len(rows)} schemas from {csv_path.name}")
        return rows
    except Exception as e:
        print(f"Error reading schema CSV '{csv_path}': {e}")
        return []

def _pick_random_schema(schemas: list[dict], max_attempts: int = 5) -> Optional[dict]:
    """
    Picks a random schema and parses its JSON content.
    Enhanced to handle markdown code blocks and malformed JSON.
    """
    if not schemas:
        return None
    
    available_schemas = schemas.copy()
    attempts = 0
    
    while available_schemas and attempts < max_attempts:
        attempts += 1
        choice = random.choice(available_schemas)
        available_schemas.remove(choice)
        
        try:
            json_content = choice["json_schema"]
            
            # Clean up markdown code blocks if present
            if "```json" in json_content:
                import re
                # Extract JSON from markdown code blocks
                match = re.search(r'```json\s*(.*?)\s*```', json_content, re.DOTALL)
                if match:
                    json_content = match.group(1)
            elif "```" in json_content:
                # Remove any other code block markers
                json_content = re.sub(r'```[^\n]*\n?', '', json_content)
                json_content = re.sub(r'\n?```', '', json_content)
            
            # Clean up double-escaped quotes
            json_content = json_content.replace('""', '"')
            
            # Try to parse the cleaned JSON
            parsed_schema = json.loads(json_content)
            print(f"✅ Successfully parsed schema '{choice.get('name', 'Unknown')}'")
            return parsed_schema
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse schema '{choice.get('name', 'Unknown')}' (attempt {attempts}): {e}")
            continue
        except Exception as e:
            print(f"⚠️ Error processing schema '{choice.get('name', 'Unknown')}': {e}")
            continue
    
    print(f"❌ Failed to parse any schema after {attempts} attempts")
    return None

def _pick_random_schema_with_fallback(primary_schemas: list[dict], fallback_schemas: list[dict] = None) -> Optional[dict]:
    """
    Try to pick from primary schemas first, then fallback schemas if all fail.
    """
    # Try primary schemas first
    schema = _pick_random_schema(primary_schemas, max_attempts=5)
    if schema:
        return schema
    
    # If primary schemas all fail, try fallback schemas
    if fallback_schemas:
        print("🔄 Primary schemas failed, trying fallback schemas...")
        schema = _pick_random_schema(fallback_schemas, max_attempts=5)
        if schema:
            return schema
    
    # Last resort: try default schemas
    print("🔄 All schemas failed, using default schemas...")
    return _pick_random_schema(DEFAULT_ROWS, max_attempts=2)

def _get_schema_by_type(schema_type: str, session_id: str = None) -> tuple[list[dict], str]:
    """
    Get schemas based on the selected schema type.
    """
    regen_count = _get_regeneration_count(session_id)
    
    if schema_type == "dental":
        # Use schema3.csv for dental & medical
        if SCHEMA3_CSV_PATH.exists():
            schemas = _load_schemas_from_csv(SCHEMA3_CSV_PATH)
            if schemas:
                print(f"🦷 Using DENTAL schema (schema3.csv) for session {session_id}")
                return schemas, "schema3.csv"
    
    elif schema_type == "medspa" or schema_type == "medical-aesthetics":
        # Use schema2.csv for medspa/fashion & beauty with priority system
        if regen_count < MAX_SCHEMA2_USES and SCHEMA2_CSV_PATH.exists():
            schemas = _load_schemas_from_csv(SCHEMA2_CSV_PATH)
            if schemas:
                remaining = MAX_SCHEMA2_USES - regen_count
                print(f"💄 Using MEDSPA schema (schema2.csv) - {remaining} uses remaining for session {session_id}")
                return schemas, f"schema2.csv"
    
    # Fallback to default schema.csv for both types
    if SCHEMA_CSV_PATH.exists():
        schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
        if schemas:
            print(f"📋 Using fallback schema (schema.csv) for session {session_id}")
            return schemas, "schema.csv"
    
    # Last resort: default schemas
    print(f"🔄 Using default schemas for session {session_id}")
    return DEFAULT_ROWS, "default"

def _get_priority_schemas(session_id: str = None) -> tuple[list[dict], str]:
    """
    Get schemas with priority system and fallback handling:
    - First 7 regenerations: use schema2.csv with schema.csv as fallback
    - After 7: use schema.csv with default as fallback
    """
    regen_count = _get_regeneration_count(session_id)
    
    # Priority 1: schema2.csv for first 7 regenerations
    if regen_count < MAX_SCHEMA2_USES and SCHEMA2_CSV_PATH.exists():
        schema2_schemas = _load_schemas_from_csv(SCHEMA2_CSV_PATH)
        if schema2_schemas:
            remaining = MAX_SCHEMA2_USES - regen_count
            print(f"🎯 Using PRIORITY schema2.csv ({remaining} uses remaining) for session {session_id}")
            return schema2_schemas, f"schema2.csv"
    
    # Priority 2: schema.csv (default or fallback)
    schema1_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
    if schema1_schemas:
        print(f"📋 Using schema.csv for session {session_id}")
        return schema1_schemas, "schema.csv"
    
    # Fallback: default schemas
    print(f"🔄 Using default schemas for session {session_id}")
    return DEFAULT_ROWS, "default"

def _inline_schema_from_text(text: str) -> Optional[dict]:
    """Finds the first valid JSON object in the user's text."""
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            return None
    return None

def schema_extraction(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced schema extraction with schema type selection support."""
    print("--- Running Schema Extraction Node ---")
    
    text = state.get("text", "")
    force_random = bool((state.get("metadata") or {}).get("regenerate"))
    is_new_design = state.get("context", {}).get("intent", {}).get("is_new_design", False)
    
    # Get session ID for session-aware regeneration counting
    session_id = state.get("session_id")
    if session_id:
        print(f"🆔 Processing schema extraction for session: {session_id}")
    
    # Get schema type from metadata (new feature)
    metadata = state.get("metadata", {})
    schema_type = metadata.get("schema_type", "medspa")  # Default to medspa for backward compatibility
    
    is_regeneration_request = force_random or is_new_design
    inline_schema = None if force_random else _inline_schema_from_text(text)
    
    schema = None
    schema_source = "none"

    if inline_schema:
        schema = inline_schema
        schema_source = "inline"
    else:
        if is_regeneration_request:
            _increment_regeneration_count(session_id)
        
        # Get schemas based on selected type
        primary_schemas, source_info = _get_schema_by_type(schema_type, session_id)
        
        # Load fallback schemas based on type
        if schema_type == "dental":
            # For dental, fallback to schema.csv then defaults
            fallback_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
            schema = _pick_random_schema_with_fallback(primary_schemas, fallback_schemas)
            if schema:
                schema_source = f"dental_schema (schema3.csv with fallback)"
        elif schema_type == "medspa" or schema_type == "medical-aesthetics":
            # For medspa, use priority system with schema2.csv
            if "schema2.csv" in source_info:
                # If using schema2.csv, have schema.csv as fallback
                fallback_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
                schema = _pick_random_schema_with_fallback(primary_schemas, fallback_schemas)
                if schema:
                    schema_source = f"medspa_schema (schema2.csv with fallback)"
            else:
                # If using schema.csv, have defaults as fallback
                schema = _pick_random_schema_with_fallback(primary_schemas, DEFAULT_ROWS)
                if schema:
                    schema_source = f"medspa_schema (schema.csv with fallback)"
        
        if not schema:
            print("❌ All schema sources failed")
            # Last resort: create a minimal default schema
            schema = {
                "title": "SimpleApp",
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "content": {"type": "object"}
                },
                "required": ["header", "content"]
            }
            schema_source = "emergency_default"

    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    gi["user_text"] = text
    gi["json_schema"] = schema
    gi["schema_source"] = schema_source
    gi["schema_type"] = schema_type  # Add schema type to generator input
    
    # CRITICAL: Add color palette to generator input during regeneration
    color_palette = state.get("color_palette", "")
    gi["color_palette"] = color_palette
    
    # Add debug logging for color palette and schema type
    print(f"🎨 Schema Extraction - Color Palette: '{color_palette}'")
    print(f"🏥 Schema Extraction - Schema Type: '{schema_type}'")
    if color_palette and color_palette.strip():
        print(f"✅ Color palette will be used in design generation")
    else:
        print(f"❌ No color palette provided or empty")

    ctx["generator_input"] = gi
    state["context"] = ctx
    schema_to_type = {
    "schema2.csv": "medspa",
    "schema3.csv": "dental",
    "schema.csv": "medspa"
    }
    website_type = schema_to_type.get(source_info.lower(), schema_type)
    state["website_type"] = website_type

    return state

# Utility function to manually reset the counter (for testing/debugging)
def reset_schema_priority_counter(session_id: str = None):
    """Reset the regeneration counter for a specific session - useful for testing."""
    _reset_regeneration_count(session_id)