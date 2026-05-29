"""Configuration management for local agent."""

import json
import os
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Config file is in project root, not in localagent package
# 查找 config.json（从当前目录向上查找）
def find_config_file():
    """向上查找 config.json 文件"""
    current_dir = Path.cwd()
    for _ in range(3):  # 最多向上查找 3 级目录
        config_file = current_dir / "config.json"
        if config_file.exists():
            return config_file
        current_dir = current_dir.parent
        if current_dir == current_dir.parent:  # 到达根目录
            break
    # 如果找不到，返回项目根目录的预期位置
    return Path(__file__).parent.parent.parent / "config.json"

CONFIG_FILE = find_config_file()

print(f"[DEBUG] Config file path: {CONFIG_FILE}")
print(f"[DEBUG] Config file exists: {CONFIG_FILE.exists()}")

def _to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])

class BaseConfig(BaseModel):
    """Base model that accepts both camelCase and snake_case keys."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
    )

class ProviderConfig(BaseConfig):
    """Provider configuration for a single LLM provider."""

    api_key: str | None = None
    api_base: str | None = None
    extra_headers: dict[str, str] | None = None

class ProvidersConfig(BaseModel):
    """Configuration for multiple LLM providers."""

    custom: ProviderConfig = Field(default_factory=ProviderConfig)
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    moonshot: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)

class AgentConfig(BaseModel):
    """Agent configuration."""

    max_iterations: int = 20
    temperature: float = 0.7
    model: str = "deepseek-chat"
    provider: str = "auto"  # Provider name or "auto" for auto-detection

class LocalAgentConfig(BaseModel):
    """Root configuration for local agent."""

    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)

    _PROVIDER_KEYWORDS = {
        "anthropic": ["anthropic", "claude", "claude-opus", "claude-sonnet", "claude-haiku"],
        "openai": ["openai", "gpt", "o1"],
        "openrouter": ["openrouter"],
        "deepseek": ["deepseek"],
        "groq": ["groq", "llama"],
        "zhipu": ["zhipu", "glm"],
        "moonshot": ["moonshot"],
        "gemini": ["gemini"],
    }

    _PROVIDER_DEFAULT_BASES = {
        "anthropic": "https://api.anthropic.com",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
        "moonshot": "https://api.moonshot.cn/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
    }

    def _match_provider(
        self, model: str | None = None
    ) -> tuple[ProviderConfig | None, str | None]:
        """Match provider config and its name. Returns (config, name)."""
        forced = self.agent.provider
        if forced != "auto":
            p = getattr(self.providers, forced, None)
            if p:
                return p, forced
            print(f"[DEBUG] Forced provider '{forced}' not found in providers")
            return None, None

        model_lower = (model or self.agent.model).lower()
        model_prefix = model_lower.split("/", 1)[0] if "/" in model_lower else ""
        normalized_prefix = model_prefix.replace("-", "_")

        def _kw_matches(kw: str) -> bool:
            kw = kw.lower()
            return kw in model_lower or kw.replace("-", "_") in model_lower

        # Explicit provider prefix wins
        for name in self._PROVIDER_KEYWORDS:
            p = getattr(self.providers, name, None)
            if p and normalized_prefix == name:
                if p.api_key or p.api_base:
                    return p, name

        # Match by keyword
        for name, keywords in self._PROVIDER_KEYWORDS.items():
            p = getattr(self.providers, name, None)
            if p and any(_kw_matches(kw) for kw in keywords):
                if p.api_key or p.api_base:
                    return p, name

        # Fallback to providers with api_key configured
        for name in self._PROVIDER_KEYWORDS:
            p = getattr(self.providers, name, None)
            if p and p.api_key:
                return p, name

        return None, None

    def get_provider(self, model: str | None = None) -> ProviderConfig | None:
        """Get matched provider config."""
        p, _ = self._match_provider(model)
        return p

    def get_provider_name(self, model: str | None = None) -> str | None:
        """Get name of matched provider."""
        _, name = self._match_provider(model)
        return name

    def get_api_key(self, model: str | None = None) -> str | None:
        """Get API key for the given model."""
        p = self.get_provider(model)
        return p.api_key if p else None

    def get_api_base(self, model: str | None = None) -> str | None:
        """Get API base URL for given model."""
        p = self.get_provider(model)
        if p and p.api_base:
            return p.api_base

        name = self.get_provider_name(model)
        if name:
            return self._PROVIDER_DEFAULT_BASES.get(name)

        return None

    def resolve_env_vars(self) -> "LocalAgentConfig":
        """Resolve ${VAR} environment variable references."""
        data = self.dict(by_alias=True)
        data = _resolve_env_vars(data)
        return LocalAgentConfig.parse_obj(data)

def _resolve_env_vars(obj: object) -> object:
    """Recursively resolve ${VAR} patterns in string values."""
    if isinstance(obj, str):
        return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", _env_replace, obj)
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj

def _env_replace(match: re.Match[str]) -> str:
    name = match.group(1)
    value = os.environ.get(name)
    if value is None:
        raise ValueError(
            f"Environment variable '{name}' referenced in config is not set"
        )
    return value

def load_config() -> LocalAgentConfig:
    """Load configuration from file or create default."""
    config = LocalAgentConfig()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = LocalAgentConfig.parse_obj(data)
            print(f"[DEBUG] Config loaded from {CONFIG_FILE}")
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Failed to load config: {e}")
            print("Using default configuration.")
    else:
        print(f"[DEBUG] Config file not found at {CONFIG_FILE}")
        print("Using default configuration.")

    return config

def save_config(config: LocalAgentConfig) -> None:
    """Save configuration to file."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(
                config.dict(by_alias=True),
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception as e:
        print(f"Warning: Failed to save config: {e}")
