# llm.py
import json
import os
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

# Global fallback state to remember which provider is working
_FALLBACK_STATE = {
    "k2_provider": "groq",  # Start with Groq, fallback to openrouter
    "last_failure": None
}

# Friendly → provider-specific model IDs
MODEL_ALIASES: Dict[str, Dict[str, str]] = {
    "k2": {"provider": "k2-fallback", "model": "moonshotai/kimi-k2-instruct"},
    "k2-fallback": {"provider": "k2-fallback", "model": "moonshotai/kimi-k2-instruct"},
    "claude": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240229"},
    "claude-haiku": {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
    "gpt-4": {"provider": "openai", "model": "gpt-4o"},
    "gpt-4o": {"provider": "openai", "model": "gpt-4o"},
    "gpt-4o-mini": {"provider": "openai", "model": "gpt-4o-mini"},
    "gpt-4-turbo": {"provider": "openai", "model": "gpt-4-turbo"},
    "gpt-5": {"provider": "openai", "model": "gpt-5"},
    "claude-3-sonnet-20240229": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240229"},
    "claude-3-5-sonnet-20240620": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},
    "sonnet-4": {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},
    "glm-4.5": {"provider": "openrouter", "model": "z-ai/glm-4.5"},
    "groq-default": {"provider": "groq", "model": "moonshotai/kimi-k2-instruct-0905"},
    "groq-kimi": {"provider": "groq", "model": "moonshotai/kimi-k2-0905"},
}

def _resolve_model(model_name: Optional[str]) -> Dict[str, str]:
    """
    Resolve a friendly model name to a provider + model id.
    Falls back to k2 (which has automatic fallback).
    """
    key = (model_name or "k2").strip()
    # Allow passing full provider ids directly (e.g., 'claude-3-5-sonnet-20240229')
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    # Heuristic: infer provider by prefix
    if key.startswith("gpt-"):
        return {"provider": "openai", "model": key}
    if key.startswith("claude-"):
        return {"provider": "anthropic", "model": key}
    if key.startswith("groq"):
        return {"provider": "groq", "model": "moonshotai/kimi-k2-instruct-0905"}
    if key.startswith("k2"):
        return {"provider": "k2-fallback", "model": "moonshotai/kimi-k2-instruct"}
    # Default
    return MODEL_ALIASES["k2"]

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

def _make_openrouter(model_id: str, **kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        model="moonshotai/kimi-k2",  # Correct OpenRouter model ID
        temperature=kwargs.get("temperature", 0.3),
        max_retries=kwargs.get("max_retries", 2),
        timeout=kwargs.get("timeout", 60),
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
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

def _get_k2_model_with_fallback(**kwargs) -> Any:
    """
    Get K2 model with intelligent fallback that remembers the working provider.
    """
    global _FALLBACK_STATE
    
    # If we already know OpenRouter works, use it directly
    if _FALLBACK_STATE["k2_provider"] == "openrouter":
        if _has_key("OPENROUTER_API_KEY"):
            print("✅ Using OpenRouter K2 model (cached working provider)")
            return _make_openrouter("moonshotai/kimi-k2-0905", **kwargs)
    
    # Try Groq first (unless we know it's failing)
    if _FALLBACK_STATE["k2_provider"] == "groq" and _has_key("GROQ_API_KEY"):
        try:
            groq_model = _make_groq("moonshotai/kimi-k2-instruct-0905", **kwargs)
            # Test the model with a simple call
            test_messages = [HumanMessage(content="Hello")]
            groq_model.invoke(test_messages)
            print("✅ Using Groq K2 model")
            return groq_model
        except Exception as e:
            print(f"⚠️ Groq K2 failed: {e}. Switching to OpenRouter...")
            _FALLBACK_STATE["k2_provider"] = "openrouter"
            _FALLBACK_STATE["last_failure"] = str(e)
    
    # Use OpenRouter as fallback
    if _has_key("OPENROUTER_API_KEY"):
        print("✅ Using OpenRouter K2 model (fallback)")
        _FALLBACK_STATE["k2_provider"] = "openrouter"
        return _make_openrouter("moonshotai/kimi-k2", **kwargs)
    
    # If no OpenRouter key, try other fallbacks
    print("⚠️ No OpenRouter key; trying other providers...")
    if _has_key("OPENAI_API_KEY"):
        return _make_openai("gpt-4o", **kwargs)
    if _has_key("ANTHROPIC_API_KEY"):
        return _make_anthropic("claude-3-5-sonnet-20240620", **kwargs)
    
    raise RuntimeError("No available LLM API keys for K2 fallback. Set GROQ_API_KEY and/or OPENROUTER_API_KEY.")

@traceable(name="get_chat_model", run_type="tool")
def get_chat_model(model_name: Optional[str] = None, **kwargs) -> Any:
    """
    Get the appropriate chat model based on model name.
    For K2 models, automatically fallback from Groq to OpenRouter if needed.
    """
    resolved = _resolve_model(model_name)
    provider = resolved["provider"]
    model_id = resolved["model"]

    # Special handling for K2 with automatic fallback
    if provider == "k2-fallback":
        return _get_k2_model_with_fallback(**kwargs)

    if provider == "openai":
        if _has_key("OPENAI_API_KEY"):
            return _make_openai(model_id, **kwargs)
        print("⚠️ OPENAI_API_KEY missing; falling back to K2.")
        return _get_k2_model_with_fallback(**kwargs)

    if provider == "anthropic":
        if _has_key("ANTHROPIC_API_KEY"):
            return _make_anthropic(model_id, **kwargs)
        print("⚠️ ANTHROPIC_API_KEY missing; falling back to K2.")
        return _get_k2_model_with_fallback(**kwargs)

    # ✅ ADDED: OpenRouter provider handler
    if provider == "openrouter":
        if _has_key("OPENROUTER_API_KEY"):
            print(f"✅ Using OpenRouter model: {model_id}")
            return _make_openrouter(model_id, **kwargs)
        print("⚠️ OPENROUTER_API_KEY missing; falling back to K2.")
        return _get_k2_model_with_fallback(**kwargs)

    if provider == "groq":
        if _has_key("GROQ_API_KEY"):
            return _make_groq(model_id, **kwargs)
        print("⚠️ GROQ_API_KEY missing; falling back to K2.")
        return _get_k2_model_with_fallback(**kwargs)

    raise RuntimeError("No available LLM API keys. Set GROQ_API_KEY or OPENROUTER_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY.")

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