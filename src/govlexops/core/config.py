"""Pipeline runtime config loader (YAML + pydantic)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KRLawConfig(BaseModel):
    queries: list[str] = Field(default_factory=list)
    max_per_query: int = 80
    issued_since_year_offset: int = -3


class KRDecreeConfig(BaseModel):
    queries: list[str] = Field(
        default_factory=lambda: ["시행령", "대통령령", "총리령", "부령"]
    )
    max_per_query: int = 40
    issued_since_year_offset: int = -3
    target: str = "ordin"


class USCongressConfig(BaseModel):
    congress: int = 118
    max_count: int = 250
    min_intro_year_offset: int = -3


class KRAssemblyConfig(BaseModel):
    assemblies: list[str] = Field(default_factory=lambda: ["제21대", "제22대"])
    test_limit: int | None = 5000
    page_size: int = 100
    start_year_offset: int = -3
    end_year_offset: int = -1


class PipelineConfig(BaseModel):
    store_backend: str = "jsonl"
    sqlite_path: str = "data_index/normalized/docs.sqlite"
    kr_law: KRLawConfig = Field(default_factory=KRLawConfig)
    kr_decree: KRDecreeConfig = Field(default_factory=KRDecreeConfig)
    us_congress: USCongressConfig = Field(default_factory=USCongressConfig)
    kr_assembly: KRAssemblyConfig = Field(default_factory=KRAssemblyConfig)


class RuntimeSettings(BaseSettings):
    """Runtime settings for selecting config profile."""

    model_config = SettingsConfigDict(env_prefix="GOVLEX_", extra="ignore")
    config_path: str = "configs/pipeline.yaml"


def load_pipeline_config(path: str | Path | None = None) -> PipelineConfig:
    config_path = Path(path or RuntimeSettings().config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return PipelineConfig.model_validate(raw)
