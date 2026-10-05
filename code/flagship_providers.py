"""Adapters for the current flagship models, with tool results fed back to the model.

providers.py is hashed by the sealed Study 2 and Study 3 designs and is never
edited. The flagship models also need different requests: OpenAI's are served
through the Responses API, Anthropic's think adaptively, and Gemini returns
thought signatures that a second turn must carry back. This module is the only
place those differences live.

A Conversation holds one trial's messages in the provider's own format.

    chat = Conversation("anthropic", "claude-opus-5-5", spec, max_tokens=4096)
    reply = chat.step()                       # one model call
    chat.tool_result(reply, "missing required parameter", is_error=True)
    reply = chat.step()                       # the model reacts

Sampling settings are the provider defaults: no temperature, effort or thinking
budget is sent. Every adapter records the model's FIRST tool call, as providers.py does.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import json

import providers


class Conversation:
    def __init__(self, provider, model, spec, max_tokens):
        if provider not in _STEP:
            raise ValueError(f"no flagship adapter for provider {provider!r}")
        self.provider, self.model, self.spec, self.max_tokens = provider, model, spec, max_tokens
        self.items = []       # provider-native turns after the first user message
        self.client = None

    def step(self):
        """One model call. Returns the reply in the shape providers.call() uses, plus
        call_id, usage (input tokens, output tokens incl. thinking) and served_model."""
        reply = _STEP[self.provider](self)
        reply["served_model"] = providers.served_model(reply["raw"])
        reply["identity_status"] = providers.check_served_model(self.model, reply["raw"])
        return reply

    def tool_result(self, reply, content, is_error=False):
        """Append the model's own turn and the tool's answer to it."""
        _RESULT[self.provider](self, reply, content, is_error)


def _reply(text, calls, raw, usage, native):
    """calls: [(name, arguments or raw string, call id)] in the order the model made them."""
    out = {"text": text, "tool_called": bool(calls), "tool_name": None, "params": {},
           "parse_error": None, "call_id": None, "tool_calls": len(calls),
           "raw": raw, "usage": usage, "_native": native}
    if calls:
        name, arguments, call_id = calls[0]
        out.update(tool_name=name, call_id=call_id)
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except (json.JSONDecodeError, TypeError) as error:
                out["parse_error"], arguments = str(error), {"_raw_arguments": arguments}
        out["params"] = arguments
    return out


# --- Anthropic ---------------------------------------------------------------
def _anthropic_step(chat):
    from anthropic import Anthropic
    chat.client = chat.client or Anthropic()
    tool = chat.spec["tool"]
    response = chat.client.messages.create(
        model=chat.model, max_tokens=chat.max_tokens, system=chat.spec["system"],
        tools=[{"name": tool["name"], "description": tool["description"],
                "input_schema": tool["parameters"]}],
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": chat.spec["user"]}] + chat.items)
    text = "".join(block.text for block in response.content if block.type == "text")
    calls = [(block.name, dict(block.input or {}), block.id)
             for block in response.content if block.type == "tool_use"]
    usage = response.usage
    tokens_in = (usage.input_tokens + (getattr(usage, "cache_creation_input_tokens", 0) or 0)
                 + (getattr(usage, "cache_read_input_tokens", 0) or 0))
    return _reply(text, calls, providers._dump(response), (tokens_in, usage.output_tokens), response.content)


def _anthropic_result(chat, reply, content, is_error):
    chat.items.append({"role": "assistant", "content": reply["_native"]})
    chat.items.append({"role": "user", "content": [{
        "type": "tool_result", "tool_use_id": reply["call_id"], "content": content, "is_error": is_error}]})


# --- OpenAI (Responses API) --------------------------------------------------
def _openai_step(chat):
    from openai import OpenAI
    chat.client = chat.client or OpenAI()
    tool = chat.spec["tool"]
    response = chat.client.responses.create(
        model=chat.model, max_output_tokens=chat.max_tokens, instructions=chat.spec["system"],
        tools=[{"type": "function", "name": tool["name"], "description": tool["description"],
                "parameters": tool["parameters"], "strict": False}],
        tool_choice="auto", store=False, include=["reasoning.encrypted_content"],
        input=[{"role": "user", "content": chat.spec["user"]}] + chat.items)
    calls = [(item.name, item.arguments, item.call_id)
             for item in response.output if item.type == "function_call"]
    usage = (response.usage.input_tokens, response.usage.output_tokens)
    native = [item.model_dump(exclude_none=True) for item in response.output]
    return _reply(response.output_text or "", calls, providers._dump(response), usage, native)


def _openai_result(chat, reply, content, is_error):
    chat.items.extend(reply["_native"])
    chat.items.append({"type": "function_call_output", "call_id": reply["call_id"], "output": content})


# --- Google ------------------------------------------------------------------
def _google_step(chat):
    from google import genai
    from google.genai import types
    chat.client = chat.client or genai.Client()
    tool = chat.spec["tool"]
    declaration = types.FunctionDeclaration(
        name=tool["name"], description=tool["description"], parameters_json_schema=tool["parameters"])
    config = types.GenerateContentConfig(
        system_instruction=chat.spec["system"], max_output_tokens=chat.max_tokens,
        tools=[types.Tool(function_declarations=[declaration])])
    first = types.Content(role="user", parts=[types.Part(text=chat.spec["user"])])
    response = chat.client.models.generate_content(model=chat.model, contents=[first] + chat.items, config=config)
    candidates = getattr(response, "candidates", None) or []
    content = getattr(candidates[0], "content", None) if candidates else None
    parts = getattr(content, "parts", None) or []
    text = "".join(part.text for part in parts if getattr(part, "text", None) and not getattr(part, "thought", False))
    calls = [(part.function_call.name, dict(part.function_call.args or {}), part.function_call.id)
             for part in parts if getattr(part, "function_call", None)]
    usage = response.usage_metadata
    tokens_in = (usage.prompt_token_count or 0) + (usage.tool_use_prompt_token_count or 0)
    tokens_out = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return _reply(text, calls, providers._dump(response), (tokens_in, tokens_out), content)


def _google_result(chat, reply, content, is_error):
    from google.genai import types
    chat.items.append(reply["_native"])
    key = "error" if is_error else "result"
    chat.items.append(types.Content(role="user", parts=[types.Part.from_function_response(
        name=reply["tool_name"], response={key: content})]))


_STEP = {"anthropic": _anthropic_step, "openai": _openai_step, "google": _google_step}
_RESULT = {"anthropic": _anthropic_result, "openai": _openai_result, "google": _google_result}
