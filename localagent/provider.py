"""Minimal LLM provider abstraction."""

from dataclasses import dataclass, field
from typing import Any
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
    """Minimal OpenAI-compatible provider."""

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
                timeout=120.0,
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

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Send chat completion request."""
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if tools:
            payload["tools"] = tools

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
        except Exception as e:
            print(f"[ERROR] Request failed: {type(e).__name__}: {e}")
            raise

        choice = data["choices"][0]
        message = choice["message"]

        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                args = tc["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=args,
                ))

        return LLMResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason", "stop"),
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
