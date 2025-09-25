# nodes/schema_extraction_node.py
from typing import Dict, Any, Optional
import json, re, csv, random
from pathlib import Path

SCHEMA_CSV_PATH = Path(__file__).parent.parent / "schema.csv"
SCHEMA2_CSV_PATH = Path(__file__).parent.parent / "schema2.csv"
SCHEMA3_CSV_PATH = Path(__file__).parent.parent / "schema3.csv"
REGENERATION_COUNTER_FILE = Path(__file__).parent.parent / "regeneration_counter.json"

MAX_SCHEMA2_USES = 5

DEFAULT_ROWS = [
    {
        "name": "UserProfile",
        "json_schema": json.dumps(
            {
                "title": "UserProfile",
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
                "required": ["id", "name", "email"],
            }
        ),
    },
    {
        "name": "Product",
        "json_schema": json.dumps(
            {
                "title": "Product",
                "type": "object",
                "properties": {
                    "sku": {"type": "string"},
                    "title": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["sku", "title"],
            }
        ),
    },
]


def _get_regeneration_count(session_id: str = None) -> int:
    """Get the current regeneration count from persistent storage for a specific session."""
    try:
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)

                if not session_id:
                    return data.get("count", 0)

                return data.get("sessions", {}).get(session_id, 0)
    except Exception as e:
        print(f"⚠️ Error reading regeneration counter: {e}")
    return 0


def _increment_regeneration_count(session_id: str = None) -> int:
    """Increment and save the regeneration count for a specific session."""
    try:

        data = {}
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)

        if "sessions" not in data:
            data["sessions"] = {}

        current_count = (
            data["sessions"].get(session_id, 0) if session_id else data.get("count", 0)
        )
        new_count = current_count + 1

        if session_id:
            data["sessions"][session_id] = new_count

        else:

            data["count"] = new_count

        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump(data, f)

        return new_count
    except Exception as e:

        return 0


def _reset_regeneration_count(session_id: str = None):
    """Reset regeneration count for a specific session (for testing or manual reset)."""
    try:

        data = {}
        if REGENERATION_COUNTER_FILE.exists():
            with REGENERATION_COUNTER_FILE.open("r") as f:
                data = json.load(f)

        if "sessions" not in data:
            data["sessions"] = {}

        if session_id:
            data["sessions"][session_id] = 0

        else:

            data["count"] = 0

        with REGENERATION_COUNTER_FILE.open("w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"⚠️ Error resetting regeneration counter: {e}")


def _load_schemas_from_csv(csv_path: Path) -> list[dict]:
    """Loads all valid schemas from the specified CSV file."""
    if not csv_path.exists():

        return []

    rows = []
    try:
        with csv_path.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:

                json_schema = row.get("json_schema") or row.get("JSON SCHEMA")
                name = row.get("name") or row.get("S.No", "Unknown")

                if name and json_schema:
                    rows.append({"name": name, "json_schema": json_schema})

        return rows
    except Exception as e:

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

            if "```json" in json_content:
                import re

                match = re.search(r"```json\s*(.*?)\s*```", json_content, re.DOTALL)
                if match:
                    json_content = match.group(1)
            elif "```" in json_content:

                json_content = re.sub(r"```[^\n]*\n?", "", json_content)
                json_content = re.sub(r"\n?```", "", json_content)

            json_content = json_content.replace('""', '"')

            parsed_schema = json.loads(json_content)

            return parsed_schema

        except json.JSONDecodeError as e:

            continue
        except Exception as e:

            continue

    return None


def _pick_random_schema_with_fallback(
    primary_schemas: list[dict], fallback_schemas: list[dict] = None
) -> Optional[dict]:
    """
    Try to pick from primary schemas first, then fallback schemas if all fail.
    """

    schema = _pick_random_schema(primary_schemas, max_attempts=5)
    if schema:
        return schema

    if fallback_schemas:

        schema = _pick_random_schema(fallback_schemas, max_attempts=5)
        if schema:
            return schema

    return _pick_random_schema(DEFAULT_ROWS, max_attempts=2)


def _get_schema_by_type(
    schema_type: str, session_id: str = None
) -> tuple[list[dict], str]:
    """
    Get schemas based on the selected schema type.
    """
    regen_count = _get_regeneration_count(session_id)

    if schema_type == "dental":

        if SCHEMA3_CSV_PATH.exists():
            schemas = _load_schemas_from_csv(SCHEMA3_CSV_PATH)
            if schemas:

                return schemas, "schema3.csv"

    elif schema_type == "medspa" or schema_type == "medical-aesthetics":

        if regen_count < MAX_SCHEMA2_USES and SCHEMA2_CSV_PATH.exists():
            schemas = _load_schemas_from_csv(SCHEMA2_CSV_PATH)
            if schemas:
                remaining = MAX_SCHEMA2_USES - regen_count

                return schemas, f"schema2.csv"

    if SCHEMA_CSV_PATH.exists():
        schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
        if schemas:

            return schemas, "schema.csv"

    return DEFAULT_ROWS, "default"


def _get_priority_schemas(session_id: str = None) -> tuple[list[dict], str]:
    """
    Get schemas with priority system and fallback handling:
    - First 7 regenerations: use schema2.csv with schema.csv as fallback
    - After 7: use schema.csv with default as fallback
    """
    regen_count = _get_regeneration_count(session_id)

    if regen_count < MAX_SCHEMA2_USES and SCHEMA2_CSV_PATH.exists():
        schema2_schemas = _load_schemas_from_csv(SCHEMA2_CSV_PATH)
        if schema2_schemas:
            remaining = MAX_SCHEMA2_USES - regen_count

            return schema2_schemas, f"schema2.csv"

    schema1_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
    if schema1_schemas:

        return schema1_schemas, "schema.csv"

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


async def schema_extraction(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced schema extraction with schema type selection support."""

    text = state.get("text", "")
    force_random = bool((state.get("metadata") or {}).get("regenerate"))
    is_new_design = (
        state.get("context", {}).get("intent", {}).get("is_new_design", False)
    )

    session_id = state.get("session_id")
    if session_id:
        print(f"🆔 Processing schema extraction for session: {session_id}")

    metadata = state.get("metadata", {})
    schema_type = metadata.get("schema_type", "medspa")

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

        primary_schemas, source_info = _get_schema_by_type(schema_type, session_id)

        if schema_type == "dental":

            fallback_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
            schema = _pick_random_schema_with_fallback(
                primary_schemas, fallback_schemas
            )
            if schema:
                schema_source = f"dental_schema (schema3.csv with fallback)"
        elif schema_type == "medspa" or schema_type == "medical-aesthetics":

            if "schema2.csv" in source_info:

                fallback_schemas = _load_schemas_from_csv(SCHEMA_CSV_PATH)
                schema = _pick_random_schema_with_fallback(
                    primary_schemas, fallback_schemas
                )
                if schema:
                    schema_source = f"medspa_schema (schema2.csv with fallback)"
            else:

                schema = _pick_random_schema_with_fallback(
                    primary_schemas, DEFAULT_ROWS
                )
                if schema:
                    schema_source = f"medspa_schema (schema.csv with fallback)"

        if not schema:

            schema = {
                "title": "SimpleApp",
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "content": {"type": "object"},
                },
                "required": ["header", "content"],
            }
            schema_source = "emergency_default"

    ctx = state.get("context", {})
    gi = ctx.get("generator_input", {})
    gi["user_text"] = text
    gi["json_schema"] = schema
    gi["schema_source"] = schema_source
    gi["schema_type"] = schema_type

    color_palette = state.get("color_palette", "")
    gi["color_palette"] = color_palette

    if color_palette and color_palette.strip():
        print(f"✅ Color palette will be used in design generation")
    else:
        print(f"❌ No color palette provided or empty")

    ctx["generator_input"] = gi
    state["context"] = ctx
    schema_to_type = {
        "schema2.csv": "medspa",
        "schema3.csv": "dental",
        "schema.csv": "medspa",
    }
    website_type = schema_to_type.get(source_info.lower(), schema_type)
    state["website_type"] = website_type

    return state


def reset_schema_priority_counter(session_id: str = None):
    """Reset the regeneration counter for a specific session - useful for testing."""
    _reset_regeneration_count(session_id)
