# nodes/schema_extraction_node.py
from typing import Dict, Any, Optional
import json, re, csv, random
from pathlib import Path

# Schema file paths
SCHEMA_CSV_PATH = Path(__file__).parent.parent / "schema.csv"
SCHEMA2_CSV_PATH = Path(__file__).parent.parent / "schema2.csv"  # New priority schema
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

def _get_regeneration_count() -> int:
    """Get the current regeneration count from persistent storage."""
    try:
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)
                return data.get("count", 0)
    except Exception as e:
        print(f"⚠️ Error reading regeneration counter: {e}")
    return 0

def _increment_regeneration_count() -> int:
    """Increment and save the regeneration count."""
    try:
        current_count = _get_regeneration_count()
        new_count = current_count + 1
        
        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump({"count": new_count, "last_updated": json.dumps(None)}, f)
        
        print(f"📊 Regeneration count: {new_count}")
        return new_count
    except Exception as e:
        print(f"⚠️ Error updating regeneration counter: {e}")
        return 0

def _reset_regeneration_count():
    """Reset regeneration count (for testing or manual reset)."""
    try:
        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump({"count": 0, "last_updated": json.dumps(None)}, f)
        print("🔄 Regeneration counter reset to 0")
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

def _get_priority_schemas() -> tuple[list[dict], str]:
    """
    Get schemas with priority system and fallback handling:
    - First 10 regenerations: use schema2.csv with schema.csv as fallback
    - After 10: use schema.csv with default as fallback
    """
    regen_count = _get_regeneration_count()
    
    # Priority 1: schema2.csv for first 10 regenerations
    if regen_count < MAX_SCHEMA2_USES and SCHEMA2_CSV_PATH.exists():
        schema2_schemas = _load_schemas_from_csv(SCHEMA2_CSV_PATH)
        if schema2_schemas:
            remaining = MAX_SCHEMA2_USES - regen_count
            print(f"🎯 Using PRIORITY schema2.csv ({remaining} uses remaining)")
            return schema2_schemas, f"schema2.csv"
    
    # Priority 2: schema.csv (default or fallback)
    schema1_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
    if schema1_schemas:
        return schema1_schemas, "schema.csv"
    
    # Fallback: default schemas
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
    """Enhanced schema extraction with robust error handling."""
    print("--- Running Schema Extraction Node ---")
    
    text = state.get("text", "")
    force_random = bool((state.get("metadata") or {}).get("regenerate"))
    is_new_design = state.get("context", {}).get("intent", {}).get("is_new_design", False)
    
    is_regeneration_request = force_random or is_new_design
    inline_schema = None if force_random else _inline_schema_from_text(text)
    
    schema = None
    schema_source = "none"

    if inline_schema:
        schema = inline_schema
        schema_source = "inline"
    else:
        if is_regeneration_request:
            _increment_regeneration_count()
        
        # Get primary and fallback schemas
        primary_schemas, source_info = _get_priority_schemas()
        
        # For priority system, also load fallback schemas
        if "schema2.csv" in source_info:
            # If using schema2.csv, have schema.csv as fallback
            fallback_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
            schema = _pick_random_schema_with_fallback(primary_schemas, fallback_schemas)
            if schema:
                schema_source = f"csv_priority (schema2.csv with fallback)"
        else:
            # If using schema.csv, have defaults as fallback
            schema = _pick_random_schema_with_fallback(primary_schemas, DEFAULT_ROWS)
            if schema:
                schema_source = f"csv_priority (schema.csv with fallback)"
        
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

    ctx["generator_input"] = gi
    state["context"] = ctx
    return state

# Utility function to manually reset the counter (for testing/debugging)
def reset_schema_priority_counter():
    """Reset the regeneration counter - useful for testing."""
    _reset_regeneration_count()