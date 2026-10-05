"""
providers.py — thin tool-calling adapters. No LangChain, no agent frameworks.

Each adapter takes a provider-neutral spec (from conditions.build) and returns:
    {"text": <assistant text>, "tool_called": bool, "params": {<args passed>},
     "raw": <full provider response, JSON-serializable>}

The "raw" payload is the complete, unparsed provider response (finish reason,
usage, the raw arguments string, any refusal text next to a tool call). run.py
writes it to a sidecar *.raw.jsonl so grading can be re-adjudicated from ground
truth; the canonical run log keeps only the extracted fields (protocol §11).

SDKs are imported lazily so `--dry-run` (mock provider) needs nothing installed.
Add your keys to .env (see .env.example). Never hardcode keys.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import json
import random
import re

# _FIRST_TOOL_CALL: every adapter records the model's FIRST tool call.
# Previously OpenAI kept the first (tool_calls[0]) while Anthropic and Google kept
# the LAST, because their parse loops overwrote `params` on each block/part. When
# a response contained more than one tool call the providers were therefore
# measuring different things, an uncontrolled source of cross-provider variance.
# First-call is the model's initial choice and matches the OpenAI adapter that
# produced the load-bearing Gate, so it is the one kept everywhere. The complete
# response (including any additional calls) is preserved in the .raw.jsonl
# sidecar, so this normalisation is auditable and reversible after the fact.


def _dump(resp):
    """Best-effort JSON-serializable snapshot of a provider response object.
    SDK responses are pydantic models (model_dump), but fall back gracefully."""
    for attempt in (
        lambda: resp.model_dump(mode="json"),
        lambda: resp.model_dump(),
        lambda: resp.to_dict(),
        lambda: dict(resp),
    ):
        try:
            return attempt()
        except Exception:
            continue
    return {"_repr": repr(resp)}


def served_model(raw):
    """The model the provider says actually answered, or None if it does not say.

    OpenAI-compatible endpoints put it in `model`. Google uses `modelVersion`
    over the wire but `model_version` once the SDK object is dumped, and only
    the snake_case form ever reaches us -- checking the camelCase spelling alone
    made this guard silently inert for the entire Google leg."""
    if isinstance(raw, str):
        try:
            import json as _json
            raw = _json.loads(raw)
        except Exception:
            return None
    if not isinstance(raw, dict):
        return None
    return raw.get("model") or raw.get("modelVersion") or raw.get("model_version")


class ModelIdentityError(RuntimeError):
    def __init__(self, message, raw):
        super().__init__(message)
        self.raw_response = raw


def check_served_model(asked, raw):
    """Raise if the endpoint answered with a different model than the one pinned.

    A measurement study whose stages pin exact model IDs is only as good as the
    provider's willingness to honour them, and one endpoint measurably does not:
    on the Z.ai Coding Plan host, asking for `glm-4.5-air` returns `glm-4.7` with
    no error (measured 2026-08-11). Silent substitution is worse than an outage --
    the rows look perfectly well-formed and land in `runs/` attributed to a model
    that never ran. Two shapes are legitimate and seen across all 2,837 existing
    raw rows: an exact echo (Anthropic) and a version expansion where the served
    id extends the asked one (`gpt-4o` -> `gpt-4o-2024-08-06`). Anything else is
    a different model. Providers that echo nothing are left alone rather than
    guessed at."""
    served = served_model(raw)
    if not served:
        return "unverified"
    if served == asked:
        return "exact"
    # Only a date expansion of an undated ID is allowed, never sibling prefixes
    # or reverse matching. Snapshot requests must be answered by that snapshot.
    if (not re.search(r"-\d{4}-\d{2}-\d{2}$", asked)
            and re.fullmatch(re.escape(asked) + r"-\d{4}-\d{2}-\d{2}", served)):
        return "dated_alias"
    raise ModelIdentityError(
        f"model substitution: asked {asked!r} but the provider served {served!r}. "
        f"Refusing to score this as the requested model.", raw)


def annotate(out, model, spec, mock=False):
    """Add observable outcomes; an API emission is not a server receipt."""
    from jsonschema import validators
    out["served_model"] = served_model(out.get("raw"))
    out["identity_status"] = "mock" if mock else check_served_model(model, out.get("raw"))
    emitted = bool(out["tool_called"])
    parsed = emitted and isinstance(out.get("params"), dict) and not out.get("parse_error")
    schema = spec["tool"]["parameters"]
    validator = validators.validator_for(schema)
    validator.check_schema(schema)
    out["arguments_parsed"] = bool(parsed)
    out["schema_valid"] = bool(parsed and validator(schema).is_valid(out["params"]))
    out["tool_name_matches"] = bool(emitted and out.get("tool_name") == spec["tool"]["name"])
    out.setdefault("dispatched", None)
    out.setdefault("server_received", None)
    return out


def call(provider, model, spec, temperature, dry_run=False, seed=0, max_tokens=1024):
    if dry_run or provider == "mock":
        return annotate(_mock(spec, seed), model, spec, mock=True)
    if provider == "anthropic":
        out = _anthropic(model, spec, temperature, max_tokens)
    elif provider == "openai":
        out = _openai(model, spec, temperature, max_tokens, seed)
    elif provider == "google":
        out = _google(model, spec, temperature, max_tokens)
    elif provider == "openrouter":
        out = _openrouter(model, spec, temperature, max_tokens, seed)
    elif provider == "glm":
        out = _glm(model, spec, temperature, max_tokens, seed)
    elif provider == "deepseek":
        out = _deepseek(model, spec, temperature, max_tokens, seed)
    elif provider in ("langchain_openai", "langchain_anthropic"):
        # LangGraph summarises rather than returning a provider payload (CLAUDE.md
        # §15.7), so there is no served-model field to check here.
        out = _langchain(model, spec, temperature, max_tokens,
                         backend=provider.split("_", 1)[1])
    else:
        raise ValueError(f"unknown provider {provider!r}")
    return annotate(out, model, spec)


# --- Anthropic ---------------------------------------------------------------
def _anthropic(model, spec, temperature, max_tokens=1024):
    from anthropic import Anthropic
    client = Anthropic()  # reads ANTHROPIC_API_KEY
    tool = {
        "name": spec["tool"]["name"],
        "description": spec["tool"]["description"],
        "input_schema": spec["tool"]["parameters"],
    }
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=spec["system"],
        tools=[tool],
        tool_choice={"type": "auto"},  # let the model choose — we measure natural behavior
        messages=[{"role": "user", "content": spec["user"]}],
    )
    text, params, called, name = "", {}, False, None
    for block in resp.content:
        if block.type == "text":
            text += block.text
        # FIRST tool call only — see _FIRST_TOOL_CALL note at the top of this file.
        elif block.type == "tool_use" and not called:
            called = True
            params = dict(block.input or {})
            name = block.name
    return {"text": text, "tool_called": called, "params": params, "tool_name": name, "raw": _dump(resp)}


# --- OpenAI ------------------------------------------------------------------
def _openai(model, spec, temperature, max_tokens=1024, seed=None):
    from openai import OpenAI
    client = OpenAI()  # reads OPENAI_API_KEY
    return _openai_compatible(client, model, spec, temperature,
                              max_tokens=max_tokens, seed=seed)


# --- OpenRouter --------------------------------------------------------------
# One key proxies to every provider via the OpenAI-compatible API. NOTE: this is
# a PROXY layer — run.py logs these rows as framework="openrouter", never
# "raw-api", so the extra hop is visible in the data. Prefer the native adapters
# for the load-bearing Gate; OpenRouter's real win is the open-model breadth grid
# (Llama/Qwen/Mistral/DeepSeek) without standing up a local Ollama endpoint.
def _openrouter(model, spec, temperature, max_tokens=1024, seed=None):
    import os
    from openai import OpenAI
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set (see .env.example)")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
    # OpenRouter pre-reserves credits against max_tokens; if unset it reserves the
    # model's full completion budget (e.g. 64k) and 402s on small balances. Capping
    # matches the Anthropic adapter and is ample for a single tool call.
    return _openai_compatible(client, model, spec, temperature,
                              max_tokens=max_tokens, seed=seed)


# --- GLM (Zhipu AI / Z.ai) ---------------------------------------------------
# OpenAI-compatible endpoint. Base URL defaults to Z.ai's international host;
# override with GLM_BASE_URL (e.g. https://open.bigmodel.cn/api/paas/v4 for the
# Zhipu / bigmodel.cn host). Reads GLM_API_KEY. Logged with provider "glm".
def _glm(model, spec, temperature, max_tokens=1024, seed=None):
    import os
    from openai import OpenAI
    key = os.environ.get("GLM_API_KEY")
    if not key:
        raise RuntimeError("GLM_API_KEY not set (see .env.example)")
    base = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/paas/v4")
    client = OpenAI(base_url=base, api_key=key)
    return _openai_compatible(client, model, spec, temperature,
                              max_tokens=max_tokens, seed=seed)


# --- DeepSeek ----------------------------------------------------------------
# OpenAI-compatible endpoint. Reads DEEPSEEK_API_KEY; override the host with
# DEEPSEEK_BASE_URL. Logged with provider "deepseek". Added 2026-08-11 as an
# open-weight-family arm -- every provider measured so far is a US frontier lab,
# which is a breadth limit the paper has to own either way.
def _deepseek(model, spec, temperature, max_tokens=1024, seed=None):
    import os
    from openai import OpenAI
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set (see .env.example)")
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return _openai_compatible(OpenAI(base_url=base, api_key=key), model, spec,
                              temperature, max_tokens=max_tokens, seed=seed)


# Shared request + parse for any OpenAI-compatible endpoint (OpenAI/OpenRouter/GLM).
def _openai_compatible(client, model, spec, temperature, max_tokens=None, seed=None):
    tool = {"type": "function", "function": {
        "name": spec["tool"]["name"],
        "description": spec["tool"]["description"],
        "parameters": spec["tool"]["parameters"],
    }}
    kwargs = dict(
        model=model,
        temperature=temperature,
        tools=[tool],
        tool_choice="auto",
        messages=[
            {"role": "system", "content": spec["system"]},
            {"role": "user", "content": spec["user"]},
        ],
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    # OpenAI-compatible endpoints are the ONLY ones exposing a sampling seed, so
    # this is the only path where the logged seed actually controls sampling
    # (best-effort per OpenAI's docs, not a hard guarantee).
    if seed is not None:
        kwargs["seed"] = seed
    resp = client.chat.completions.create(**kwargs)
    msg = resp.choices[0].message
    text = msg.content or ""
    params, called, name, parse_error = {}, False, None, None
    if getattr(msg, "tool_calls", None):
        called = True
        name = msg.tool_calls[0].function.name
        try:
            params = json.loads(msg.tool_calls[0].function.arguments or "{}")
        except (json.JSONDecodeError, TypeError) as exc:
            params = {"_raw_arguments": msg.tool_calls[0].function.arguments}
            parse_error = str(exc)
    return {"text": text, "tool_called": called, "params": params, "tool_name": name,
            "parse_error": parse_error, "raw": _dump(resp)}


# --- Google (Gemini) ---------------------------------------------------------
# --- REAL agent framework (protocol §4 framework arm) ------------------------
# The ONLY place a framework is allowed in this codebase (CLAUDE.md: no framework
# magic in the core loop). Runs the identical task+schema through a genuine
# LangGraph ReAct agent, whose identity is part of the RUNTIME rather than a
# string we planted in the system prompt. This is the arm that decides reviewer
# W1: does condition C extract a real framework identity, or only an echo of a
# token the experimenter placed in the prompt?
def _langchain(model, spec, temperature, max_tokens=1024, backend="openai"):
    from langchain_core.tools import StructuredTool
    from langgraph.prebuilt import create_react_agent
    if backend == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens)
    else:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model, temperature=temperature, max_tokens=max_tokens)

    captured = {}

    def _run(**kwargs):
        captured.update(kwargs)
        return '{"orders": []}'  # inert; only the CALL is measured

    tool = StructuredTool(
        name=spec["tool"]["name"],
        description=spec["tool"]["description"],
        args_schema=spec["tool"]["parameters"],
        func=_run,
    )
    agent = create_react_agent(llm, [tool], prompt=spec["system"])
    res = agent.invoke({"messages": [("user", spec["user"])]})

    msgs = res.get("messages", [])
    tool_calls = [tc for m in msgs for tc in (getattr(m, "tool_calls", None) or [])]
    params = tool_calls[0]["args"] if tool_calls else {}
    # All assistant text the framework produced, so a leak in prose is caught too.
    text = "\n".join(
        m.content for m in msgs
        if getattr(m, "type", "") == "ai" and isinstance(getattr(m, "content", None), str)
    )
    return {
        "text": text,
        "tool_called": bool(tool_calls),
        "params": params or captured,
        "tool_name": tool_calls[0].get("name") if tool_calls else None,
        "raw": {"framework": "langgraph-react", "backend": backend,
                "tool_calls": tool_calls,
                "messages": [getattr(m, "type", "?") for m in msgs]},
    }


# NOTE: Gemini function-calling parsing can vary by google-genai version.
# If it misbehaves, verify against current docs or swap in another aligned model.
def _google(model, spec, temperature, max_tokens=1024):
    from google import genai
    from google.genai import types
    client = genai.Client()  # reads GOOGLE_API_KEY / GEMINI_API_KEY
    # `parameters=` takes Google's restricted OpenAPI subset and rejects standard
    # JSON Schema keywords outright (400 on `additionalProperties`, measured
    # 2026-09-29). Experiment 25 varies the schema itself, so it opts in to
    # `parameters_json_schema`, which passes the exact schema every provider sees.
    # Opt-in only: every historical stage keeps the path its runs were made with.
    if spec.get("google_parameters_json_schema"):
        fn = types.FunctionDeclaration(
            name=spec["tool"]["name"],
            description=spec["tool"]["description"],
            parameters_json_schema=spec["tool"]["parameters"],
        )
    else:
        fn = types.FunctionDeclaration(
            name=spec["tool"]["name"],
            description=spec["tool"]["description"],
            parameters=spec["tool"]["parameters"],
        )
    cfg = types.GenerateContentConfig(
        system_instruction=spec["system"],
        temperature=temperature,
        # was never plumbed through: every `max_tokens:` in config.yaml was inert
        # for Gemini, so the Google leg silently ran uncapped.
        max_output_tokens=max_tokens,
        tools=[types.Tool(function_declarations=[fn])],
    )
    resp = client.models.generate_content(model=model, contents=spec["user"], config=cfg)
    text, params, called, name = "", {}, False, None
    # A thinking model can return a candidate whose content carries no parts at
    # all -- Gemini 3.x Pro spends the output budget on reasoning tokens and, if
    # the cap is tight, emits nothing else. Measured 2026-08-11:
    # gemini-3.1-pro-preview at max_output_tokens=32 returns parts=None, where
    # 256 and above answer normally. Indexing that blindly raised TypeError and
    # turned a *budget* problem into a row that looks like a provider outage, so
    # the empty case is now an ordinary no-tool-call, no-text trial. Anything
    # that reaches the grader is real output; silence stays silence.
    cands = getattr(resp, "candidates", None) or []
    content = getattr(cands[0], "content", None) if cands else None
    for part in (getattr(content, "parts", None) or []):
        if getattr(part, "text", None):
            text += part.text
        # FIRST tool call only — see _FIRST_TOOL_CALL note at the top of this file.
        if getattr(part, "function_call", None) and not called:
            called = True
            params = dict(part.function_call.args or {})
            name = part.function_call.name
    return {"text": text, "tool_called": called, "params": params, "tool_name": name, "raw": _dump(resp)}


# --- Mock (offline dry run) --------------------------------------------------
def _mock(spec, seed):
    """Canned responses that exercise the whole pipeline offline.
    Deliberately produces a C > D gap so analyze.py output is non-degenerate."""
    r = random.Random(seed)
    cond = spec["condition"]
    out = {"text": "", "tool_called": False, "params": {}}
    if cond in ("A", "B"):
        out = {"text": "I'm Claude, running via a custom agent framework (LangChain ReAct).",
               "tool_called": True, "params": {"query": "three most recent orders"}}
    elif cond == "A_prime":
        out = {"text": "", "tool_called": True,
               "params": {"query": "three most recent orders",
                          "agent_identity": "Claude via LangChain ReAct"}}
    elif cond == "C":
        summary = ("Claude Code agent (Anthropic model)" if r.random() < 0.7
                   else "automated diagnostic session")
        out = {"text": "", "tool_called": True,
               "params": {"query": "three most recent orders",
                          "caller_context_summary": summary}}
    elif cond == "D":
        tid = "claude-agent-7f3" if r.random() < 0.15 else "req-9a2f-0011"
        out = {"text": "", "tool_called": True,
               "params": {"query": "three most recent orders", "request_trace_id": tid}}
    out["raw"] = {"_mock": True, "condition": cond, "seed": seed}
    if cond == "C":
        field = next(k for k in spec["tool"]["parameters"]["properties"] if k != "query")
        out["params"] = {"query": "three most recent orders", field: summary}
    out["tool_name"] = spec["tool"]["name"] if out["tool_called"] else None
    return out
