"""The one place doc-sync calls Gemini's generate_content: retries, a
per-call token report, and an opt-in local response cache.

Why a LOCAL cache, not Gemini's context caching: the key in use is on the
free tier, whose cached-content storage limit is 0 (a cache create was
refused with TotalCachedContentStorageTokensPerModelFreeTier, limit=0, on
2026-11-06). Context caching would only discount billing anyway, not
free-tier quota.

The local cache (DOC_SYNC_LLM_CACHE=1) instead replays a saved response
for a request that is EXACTLY the same as one already sent — same model,
same system prompt, same contents, same config — and spends nothing. Any
change at all (a different change note, an edited article, an edited
prompt or reference file) is a different key and a real call. Off by
default, so a run only replays when the person running it asked for it.

Responses are saved under doc_sync/data/llm_cache/ (git-ignored); delete
that folder to start fresh.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from google.genai import errors as genai_errors
from google.genai import types

CACHE_DIR = Path(__file__).resolve().parent / "data" / "llm_cache"
MAX_ATTEMPTS = 4


def cache_enabled():
    return os.environ.get("DOC_SYNC_LLM_CACHE", "").strip().lower() in ("1", "true", "yes", "on")


def _jsonable(contents):
    if isinstance(contents, list):
        return [_jsonable(c) for c in contents]
    if hasattr(contents, "model_dump"):
        return contents.model_dump(mode="json", exclude_none=True)  # e.g. a PDF Part: bytes -> base64
    return contents


def _cache_key(model, contents, config):
    request = {
        "model": model,
        "contents": _jsonable(contents),
        "config": config.model_dump(mode="json", exclude_none=True),
    }
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def _report(label, usage):
    if usage is None:
        return
    prompt = usage.prompt_token_count or 0
    thoughts = usage.thoughts_token_count or 0
    output = (usage.candidates_token_count or 0) + thoughts
    line = f"    (gemini {label}: {prompt:,} in / {output:,} out, {thoughts:,} of it thinking"
    if usage.cached_content_token_count:
        line += f"; {usage.cached_content_token_count:,} of the input cached by Gemini"
    print(line + ")")


def generate(gclient, model, contents, config, label):
    """gclient.models.generate_content(), retrying transient 503s with
    backoff — observed in practice on this model even back to back with a
    successful call. `label` names the call in the token report."""
    key = path = None
    if cache_enabled():
        key = _cache_key(model, contents, config)
        path = CACHE_DIR / f"{key}.json"
        if path.exists():
            print(f"    (gemini {label}: replayed from the local response cache, 0 tokens — {key[:12]})")
            return types.GenerateContentResponse.model_validate_json(path.read_text())

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = gclient.models.generate_content(model=model, contents=contents, config=config)
            break
        except genai_errors.ServerError as exc:
            if attempt == MAX_ATTEMPTS:
                raise
            wait = 5 * attempt
            print(f"    (Gemini call failed with {exc} — retrying in {wait}s, attempt {attempt}/{MAX_ATTEMPTS})")
            time.sleep(wait)
    _report(label, response.usage_metadata)

    # Only a response with a function call is worth replaying; anything
    # else is a failure the caller raises on, and should be retried live.
    if path is not None and _has_function_call(response):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(response.model_dump_json(exclude_none=True))
    return response


def _has_function_call(response):
    out = response.candidates or []
    parts = (out[0].content.parts if out and out[0].content else None) or []
    return any(getattr(p, "function_call", None) for p in parts)
