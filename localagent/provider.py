"""Minimal LLM provider abstraction with streaming support."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import httpx
import json
from functools import lru_cache

from .config import LocalAgentConfig, load_config


@lru_cache(maxsize=1)
def get_cached_config():
    return load_config()


@dataclass
class ToolCall:
    """A tool call request from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


class OpenAICompatProvider:
    """Minimal OpenAI-compatible provider with streaming support."""

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        config: LocalAgentConfig | None = None,
    ):
        self.temperature = temperature
        self._client = None

        if config is None and api_key is None:
            config = get_cached_config()

        if config is not None:
            provider_name = config.get_provider_name(model)
            self.api_key = api_key or config.get_api_key(model)
            config_api_base = config.get_api_base(model)
            self.api_base = api_base or config_api_base or "https://api.openai.com/v1"
            self.model = model or config.agent.model
        else:
            self.api_key = api_key
            self.api_base = api_base.rstrip("/") if api_base else "https://api.openai.com/v1"
            self.model = model

        if self.api_base:
            self.api_base = self.api_base.rstrip("/")

    def _get_client(self):
        if self._client is None:
            import httpx
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            extra_headers = self._get_extra_headers()
            if extra_headers:
                headers.update(extra_headers)

            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                headers=headers,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
            )
        return self._client

    def _get_extra_headers(self) -> dict[str, str]:
        try:
            config = get_cached_config()
            provider_name = config.get_provider_name(self.model)
            if provider_name:
                provider_config = getattr(config.providers, provider_name, None)
                if provider_config and provider_config.extra_headers:
                    return provider_config.extra_headers
        except Exception:
            pass
        return {}

    def _build_payload(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the request payload."""
        model_lower = self.model.lower()
        is_reasoning = any(kw in model_lower for kw in ("deepseek-v4", "deepseek-r1", "reasoner", "o1", "o3"))

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if not is_reasoning:
            payload["temperature"] = self.temperature
        if tools:
            payload["tools"] = tools
        if stream:
            payload["stream"] = True
        return payload

    @staticmethod
    def _parse_tool_calls(raw_tool_calls: list[dict]) -> list[ToolCall]:
        """Parse tool calls from API response."""
        tool_calls = []
        for tc in raw_tool_calls:
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(ToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                arguments=args,
            ))
        return tool_calls

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Send chat completion request (non-streaming)."""
        client = self._get_client()
        payload = self._build_payload(messages, tools, stream=False)

        try:
            print(f"[DEBUG] API Request: {self.api_base}/chat/completions")
            print(f"[DEBUG] Model: {self.model}")
            resp = await client.post("/chat/completions", json=payload, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] HTTP {e.response.status_code}: {e.response.text}")
            raise
        except httpx.ConnectError as e:
            print(f"[ERROR] Connection failed to {self.api_base}")
            print(f"[ERROR] Check network connection and proxy settings")
            print(f"[ERROR] Verify API key is valid: {self.api_key[:10]}...{self.api_key[-4:] if self.api_key else 'None'}")
            raise
        except httpx.ReadTimeout as e:
            print(f"[ERROR] Request timeout after 120s: {e}")
            raise RuntimeError("AI 服务响应超时，请稍后重试") from e
        except Exception as e:
            print(f"[ERROR] Request failed: {type(e).__name__}: {e}")
            raise

        choice = data["choices"][0]
        message = choice["message"]

        tool_calls = self._parse_tool_calls(message["tool_calls"]) if message.get("tool_calls") else []

        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> LLMResponse:
        """Send chat completion request with streaming.

        Yields content chunks via on_chunk callback as they arrive.
        Returns the complete LLMResponse after streaming finishes.
        """
        client = self._get_client()
        payload = self._build_payload(messages, tools, stream=True)

        print(f"[DEBUG] API Stream Request: {self.api_base}/chat/completions")
        print(f"[DEBUG] Model: {self.model}")

        content_parts: list[str] = []
        tool_calls_map: dict[int, dict[str, Any]] = {}  # index -> accumulated tool call
        finish_reason = "stop"

        try:
            async with client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason", finish_reason)

                    # Handle content streaming
                    if delta.get("content"):
                        content_parts.append(delta["content"])
                        if on_chunk:
                            await on_chunk(delta["content"])

                    # Handle tool call streaming
                    if delta.get("tool_calls"):
                        for tc_delta in delta["tool_calls"]:
                            idx = tc_delta.get("index", 0)
                            if idx not in tool_calls_map:
                                tool_calls_map[idx] = {
                                    "id": tc_delta.get("id", ""),
                                    "type": "function",
                                    "function": {
                                        "name": tc_delta.get("function", {}).get("name", ""),
                                        "arguments": tc_delta.get("function", {}).get("arguments", ""),
                                    },
                                }
                            else:
                                # Accumulate arguments
                                if tc_delta.get("id"):
                                    tool_calls_map[idx]["id"] = tc_delta["id"]
                                func_delta = tc_delta.get("function", {})
                                if func_delta.get("name"):
                                    tool_calls_map[idx]["function"]["name"] = func_delta["name"]
                                if func_delta.get("arguments"):
                                    tool_calls_map[idx]["function"]["arguments"] += func_delta["arguments"]

        except httpx.HTTPStatusError as e:
            print(f"[ERROR] Stream HTTP {e.response.status_code}: {e.response.text}")
            raise
        except httpx.ConnectError as e:
            print(f"[ERROR] Stream connection failed to {self.api_base}")
            raise
        except Exception as e:
            print(f"[ERROR] Stream request failed: {type(e).__name__}: {e}")
            # Fallback to non-streaming if streaming fails
            print("[INFO] Falling back to non-streaming request...")
            return await self.chat(messages, tools)

        # Build final response
        full_content = "".join(content_parts) if content_parts else None
        parsed_tool_calls = self._parse_tool_calls(
            list(tool_calls_map.values())
        ) if tool_calls_map else []

        return LLMResponse(
            content=full_content,
            tool_calls=parsed_tool_calls,
            finish_reason=finish_reason,
        )

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def update_config(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str | None = None,
    ) -> None:
        """Update provider configuration at runtime."""
        if api_key is not None:
            self.api_key = api_key
        if api_base is not None:
            self.api_base = api_base.rstrip("/")
        if model is not None:
            self.model = model
        self._client = None
