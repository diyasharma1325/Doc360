"""The one place doc-sync calls Claude: `claude -p` on the writer's Claude
Code login, so no ANTHROPIC_API_KEY is needed. Same pattern as the I2P
backtest harness (i2p-agent-master/.claude/skills/i2p-backtest/scripts/
harness.py): system prompt from a file, request on stdin, no tools, no
settings, no MCP servers, no slash commands, no saved session.

Structured output comes from `--json-schema`: the CLI answers with a parsed
`structured_output` object matching the schema. No regex over free text.

Three things that matter, all deliberate:

- RUN OUTSIDE THE REPO. `claude -p` still loads a CLAUDE.md found in the
  working directory or its parents, even with `--setting-sources ""`:
  measured 2026-11-06, the same call cost ~500 more input tokens from inside
  Doc360/ than from a temp folder. So every call runs from an empty temp
  folder outside the repo, and the prompt is exactly what the caller built.
- NO API KEY. ANTHROPIC_API_KEY is stripped from the child's environment, so
  a key in .env can never silently switch these calls to API billing.
- EVERY CALL IS LOGGED to data/model_calls.jsonl (model, label, seconds,
  tokens, cost as the CLI reports it), and printed in one line.

The opt-in local response cache (DOC_SYNC_LLM_CACHE=1): an exactly repeated
request (same model, system prompt, request, schema and output limit) is
replayed from data/llm_cache/ at 0 tokens. Off by default.

Claude is the only model provider (2026-11-15): the Gemini fallback was
removed, since no Gemini key can be provisioned for production.

    python3 doc_sync/claude_call.py selftest [--model claude-haiku-4-5]
"""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MODEL = "claude-sonnet-5-5"

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR = DATA_DIR / "llm_cache"
CALL_LOG = DATA_DIR / "model_calls.jsonl"

MAX_ATTEMPTS = 3
TIMEOUT_S = 1800  # one assessment returns a whole article's HTML; allow it time

_cli_cwd = None


class ClaudeCallError(RuntimeError):
    """`claude -p` failed, or answered without the structured output asked for.
    `cost` is what the failed call still spent, when the CLI reported it."""

    def __init__(self, message, cost=None):
        super().__init__(message)
        self.cost = cost


def _output_limit_hit(exc):
    """True when the response ran past the output token maximum. Never
    retried: the same request produces the same too-long answer (hit
    2026-11-11 on the Whatfix Glossary, which burned an 11-minute retry)."""
    return "output token maximum" in str(exc)


class BudgetExceeded(ClaudeCallError):
    """An agent call reached its --max-budget-usd cap before answering. Never
    retried: the same call would only reach it again. The cap is checked
    between turns, so `cost` can be somewhat over it."""


# --- cost metering ------------------------------------------------------------
# Every call's cost (as the CLI reports it, failed calls included) is added to
# each open CostMeter, so a phase can total what it spent across threads, and
# to this thread's last_cost, so a caller can read what its own call cost.
_meters = []
_meter_lock = threading.Lock()
_local = threading.local()


class CostMeter:
    """with CostMeter() as m: ... ; then m.usd and m.calls."""

    def __init__(self):
        self.usd, self.calls = 0.0, 0

    def __enter__(self):
        with _meter_lock:
            _meters.append(self)
        return self

    def __exit__(self, *exc):
        with _meter_lock:
            _meters.remove(self)
        return False


def _add_cost(cost):
    _local.last_cost = (getattr(_local, "last_cost", 0.0) or 0.0) + (cost or 0.0)
    with _meter_lock:
        for m in _meters:
            m.usd += cost or 0.0
            m.calls += 1


def take_last_cost():
    """What this thread's calls have cost since the last take_last_cost()."""
    cost = getattr(_local, "last_cost", 0.0) or 0.0
    _local.last_cost = 0.0
    return cost


def cache_enabled():
    return os.environ.get("DOC_SYNC_LLM_CACHE", "").strip().lower() in ("1", "true", "yes", "on")


def _cwd():
    """An empty folder outside the repo, made once per process. See the
    module docstring for why it must not be inside Doc360/."""
    global _cli_cwd
    if _cli_cwd is None:
        _cli_cwd = tempfile.mkdtemp(prefix="doc_sync_claude_")
    return _cli_cwd


def _cache_key(model, system, user, schema, max_tokens):
    request = {"provider": "claude-cli", "model": model, "system": system, "user": user,
               "schema": schema, "max_tokens": max_tokens}
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def _log_call(record):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CALL_LOG.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def _report(label, model, secs, usage, cost):
    fresh = usage.get("input_tokens") or 0
    cached = (usage.get("cache_read_input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0)
    out = usage.get("output_tokens") or 0
    line = f"    (claude {label}: {model}, {fresh + cached:,} in / {out:,} out, {secs:.0f}s"
    if cost is not None:
        line += f", ${cost:.4f}"
    print(line + ")", flush=True)


# The only tools a call may be given: search and read, nothing that writes or
# runs anything (agent discovery, discovery_agent.py). Anything else is refused.
READ_ONLY_TOOLS = ("Grep", "Glob", "Read")


def _run_once(model, system, user, schema, max_tokens, tools=None, cwd=None, budget_usd=None):
    """One `claude -p` call -> (structured_output dict, usage dict, cost, turns).
    `tools` (a subset of READ_ONLY_TOOLS) lets the model search and read the
    files under `cwd`; permission prompts are answered "no" automatically and
    the file tools are confined to `cwd`. Without tools, no tools at all."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(system)
        system_file = fh.name
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if max_tokens:
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_tokens)
    cmd = [
        "claude", "-p", "--model", model,
        "--system-prompt-file", system_file,
        "--json-schema", json.dumps(schema),
        "--tools", ",".join(tools or ()), "--setting-sources", "", "--strict-mcp-config",
        "--disable-slash-commands", "--no-session-persistence",
        "--output-format", "json",
    ]
    if tools:
        bad = [t for t in tools if t not in READ_ONLY_TOOLS]
        if bad:
            raise ValueError(f"only read-only tools {READ_ONLY_TOOLS} may be given, not {bad}")
        cmd += ["--allowedTools", *tools, "--permission-prompts", "none"]
    if budget_usd:
        cmd += ["--max-budget-usd", str(budget_usd)]
    try:
        proc = subprocess.run(cmd, input=user, capture_output=True, text=True,
                              cwd=cwd or _cwd(), env=env, timeout=TIMEOUT_S)
    except FileNotFoundError:
        raise ClaudeCallError("The `claude` CLI is not on PATH. Install Claude Code and log in "
                              "(`claude -p \"hi\"` should answer).")
    except subprocess.TimeoutExpired:
        raise ClaudeCallError(f"claude -p did not answer within {TIMEOUT_S}s")
    finally:
        os.unlink(system_file)

    try:
        body = json.loads(proc.stdout)
    except ValueError:
        detail = (proc.stderr or proc.stdout or "").strip()[-500:]
        raise ClaudeCallError(f"claude -p failed (exit {proc.returncode}): {detail}")
    if body.get("is_error"):
        cost = body.get("total_cost_usd")
        detail = body.get("errors") or body.get("result")
        if body.get("subtype") == "error_max_budget_usd":
            raise BudgetExceeded(f"claude -p reached its budget cap of ${budget_usd} (spent ${cost or 0:.2f}): "
                                 f"{str(detail)[:200]}", cost=cost)
        raise ClaudeCallError(f"claude -p reported an error ({body.get('subtype')}): {str(detail)[:500]}", cost=cost)
    result = body.get("structured_output")
    if not isinstance(result, dict):
        raise ClaudeCallError(
            f"claude -p answered without structured output (stop_reason="
            f"{body.get('stop_reason')!r}): {str(body.get('result'))[:300]}"
        )
    return result, body.get("usage") or {}, body.get("total_cost_usd"), body.get("num_turns")


def generate(system, user, schema, label, model=DEFAULT_MODEL, max_tokens=None, tools=None, cwd=None,
             budget_usd=None):
    """Send `user` with the `system` prompt and return the model's answer as
    a dict matching the JSON `schema`. `label` names the call in the printed
    report and the call log. Retries a failed call up to MAX_ATTEMPTS times,
    then raises ClaudeCallError. `tools`, `cwd` and `budget_usd` make it an
    agent call over the files in `cwd` (see _run_once); those are never
    cached, since the files they read can change between calls."""
    path = None
    if cache_enabled() and not tools:
        key = _cache_key(model, system, user, schema, max_tokens)
        path = CACHE_DIR / f"claude-{key}.json"
        if path.exists():
            print(f"    (claude {label}: replayed from the local response cache, 0 tokens — {key[:12]})")
            return json.loads(path.read_text())

    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.time()
        try:
            result, usage, cost, turns = _run_once(model, system, user, schema, max_tokens, tools, cwd, budget_usd)
            break
        except ClaudeCallError as exc:
            _add_cost(exc.cost)
            _log_call({"t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "label": label, "model": model, "ok": False, "error": str(exc)[:300],
                       "cost_usd": exc.cost})
            # Deterministic failures: the same request would only fail the same way.
            if attempt == MAX_ATTEMPTS or isinstance(exc, BudgetExceeded) or _output_limit_hit(exc):
                raise
            wait = 10 * attempt
            print(f"    (claude {label} failed: {exc} — retrying in {wait}s, attempt {attempt}/{MAX_ATTEMPTS})",
                  flush=True)
            time.sleep(wait)
    secs = time.time() - t0

    _report(label, model, secs, usage, cost)
    _add_cost(cost)
    _log_call({
        "t": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": label, "model": model, "ok": True, "secs": round(secs, 1),
        "input_tokens": usage.get("input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cost_usd": cost,
        **({"turns": turns} if tools else {}),
    })

    if path is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result


def main():
    parser = argparse.ArgumentParser(description="Check that claude -p works for doc-sync.")
    sub = parser.add_subparsers(dest="command", required=True)
    selftest = sub.add_parser("selftest", help="One tiny structured-output call")
    selftest.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}, "echo": {"type": "string"}},
        "required": ["ok", "echo"],
    }
    result = generate("You are a connectivity check. Answer only through the schema.",
                      "Set ok to true and echo the word 'doc-sync'.", schema, "selftest", model=args.model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
