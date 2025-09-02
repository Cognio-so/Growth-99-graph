# llm.py
import json
import os
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

# Friendly → provider-specific model IDs
MODEL_ALIASES: Dict[str, Dict[str, str]] = {
    # OpenAI
    "gpt-5": {"provider": "openai", "model": "gpt-4o"},   # alias to a stable model
    "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
    "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
    "gpt-4-turbo": {"provider": "openai", "model": "gpt-4-turbo"},
    # Anthropic
    "sonnet-4": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},  # alias
    "claude-3-sonnet-20240229": {"provider": "anthropic", "model": "claude-3-sonnet-20240229"},
    "claude-3-5-sonnet-20240620": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},
    # Groq
    "groq-default": {"provider": "groq", "model": "moonshotai/kimi-k2-instruct"},
    "groq-kimi": {"provider": "groq", "model": "moonshotai/kimi-k2-instruct"},
}

def _resolve_model(model_name: Optional[str]) -> Dict[str, str]:
    """
    Resolve a friendly model name to a provider + model id.
    Falls back to groq-default.
    """
    key = (model_name or "groq-default").strip()
    # Allow passing full provider ids directly (e.g., 'claude-3-5-sonnet-20240620')
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    # Heuristic: infer provider by prefix
    if key.startswith("gpt-"):
        return {"provider": "openai", "model": key}
    if key.startswith("claude-"):
        return {"provider": "anthropic", "model": key}
    if key.startswith("groq"):
        return {"provider": "groq", "model": "moonshotai/kimi-k2-instruct"}
    # Default
    return MODEL_ALIASES["groq-default"]

def _has_key(env_name: str) -> bool:
    v = os.getenv(env_name)
    return bool(v and v.strip())

def _make_groq(model_id: str, **kwargs) -> ChatGroq:
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=model_id,
        temperature=kwargs.get("temperature", 0.3),
        max_tokens=kwargs.get("max_tokens", 8192),
        streaming=False,  # keep non-streaming for .invoke stability
    )

def _make_openai(model_id: str, **kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_id,
        temperature=kwargs.get("temperature", 0.3),
        max_retries=kwargs.get("max_retries", 2),
        timeout=kwargs.get("timeout", 60),
    )

def _make_anthropic(model_id: str, **kwargs) -> ChatAnthropic:
    return ChatAnthropic(
        model=model_id,
        temperature=kwargs.get("temperature", 0.3),
        max_retries=kwargs.get("max_retries", 2),
        timeout=kwargs.get("timeout", 60),
    )

@traceable(name="get_chat_model", run_type="tool")
def get_chat_model(model_name: Optional[str] = None, **kwargs) -> Any:
    """
    Get the appropriate chat model based on model name.
    Falls back to Groq if provider keys are missing.
    """
    resolved = _resolve_model(model_name)
    provider = resolved["provider"]
    model_id = resolved["model"]

    if provider == "openai":
        if _has_key("OPENAI_API_KEY"):
            return _make_openai(model_id, **kwargs)
        print("⚠️ OPENAI_API_KEY missing; falling back to Groq.")
        return _make_groq(MODEL_ALIASES["groq-default"]["model"], **kwargs)

    if provider == "anthropic":
        if _has_key("ANTHROPIC_API_KEY"):
            return _make_anthropic(model_id, **kwargs)
        print("⚠️ ANTHROPIC_API_KEY missing; falling back to Groq.")
        return _make_groq(MODEL_ALIASES["groq-default"]["model"], **kwargs)

    # Groq
    if _has_key("GROQ_API_KEY"):
        return _make_groq(model_id, **kwargs)
    print("⚠️ GROQ_API_KEY missing; attempting OpenAI fallback.")
    if _has_key("OPENAI_API_KEY"):
        return _make_openai("gpt-4o", **kwargs)
    print("⚠️ OPENAI_API_KEY missing; attempting Anthropic fallback.")
    if _has_key("ANTHROPIC_API_KEY"):
        return _make_anthropic("claude-3-5-sonnet-20240620", **kwargs)

    raise RuntimeError("No available LLM API keys. Set GROQ_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY.")

@traceable(name="llm_json_call", run_type="llm")
def call_llm_json(
    chat_model: Any, 
    system_prompt: str, 
    user_prompt: str
) -> Optional[Dict[str, Any]]:
    """Call LLM and parse JSON response with tracing"""
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = chat_model.invoke(messages)
        content = response.content

        # Try to find JSON in the response first
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group(0))

        # If no JSON found, try to parse the entire content
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing JSON from LLM response: {e}")
        return None