# nodes/schema_extraction_node.py
from typing import Dict, Any, Optional
import json, re, csv, random
from pathlib import Path

# This path is relative to your project root.
# It expects a 'data' folder at the same level as your 'nodes' folder.
SCHEMA_CSV_PATH = Path(__file__).parent.parent / "schema.csv"

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

def _load_schemas_from_csv() -> list[dict]:
    """Loads all valid schemas from the specified CSV file."""
    if not SCHEMA_CSV_PATH.exists():
        print(f"Schema CSV not found at '{SCHEMA_CSV_PATH}'. Using default schemas.")
        return DEFAULT_ROWS

    rows = []
    try:
        with SCHEMA_CSV_PATH.open("r", encoding="utf-8-sig") as f: # use utf-8-sig to handle potential BOM
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both "json_schema" and "JSON SCHEMA" column names
                json_schema = row.get("json_schema") or row.get("JSON SCHEMA")
                name = row.get("name") or row.get("S.No", "Unknown")
                
                # Ensure the required columns exist and are not empty
                if name and json_schema:
                    rows.append({"name": name, "json_schema": json_schema})
        if not rows:
            print("Schema CSV is empty. Using default schemas.")
            return DEFAULT_ROWS
        return rows
    except Exception as e:
        print(f"Error reading schema CSV: {e}. Using default schemas.")
        return DEFAULT_ROWS

def _pick_random_schema(schemas: list[dict]) -> Optional[dict]:
    """Picks a random schema and parses its JSON content."""
    if not schemas:
        return None
    
    choice = random.choice(schemas)
    try:
        # The generator expects a dictionary, not a string.
        return json.loads(choice["json_schema"])
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse JSON for schema '{choice.get('name')}'.")
        return None

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
    """
    1. Tries to parse an inline JSON schema from the user's text.
    2. If not found, picks a random JSON schema from the CSV file.
    """
    print("--- Running Schema Extraction Node ---")
    text = state.get("text", "")
    force_random = bool((state.get("metadata") or {}).get("regenerate"))

    inline_schema = None if force_random else _inline_schema_from_text(text)
    
    schema = None
    schema_source = "none"

    if inline_schema:
        schema = inline_schema
        schema_source = "inline"
        print("Found inline schema in user text.")
    else:
        print("No inline schema found. Loading from CSV.")
        all_schemas = _load_schemas_from_csv()
        random_schema = _pick_random_schema(all_schemas)
        if random_schema:
            schema = random_schema
            schema_source = "csv_random"
            print(f"Randomly picked schema '{schema.get('title', 'Untitled')}' from CSV.")

    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    gi["user_text"] = text
    gi["json_schema"] = schema
    gi["schema_source"] = schema_source

    ctx["generator_input"] = gi
    state["context"] = ctx
    return state