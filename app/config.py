import os
from pathlib import Path
from typing import Optional

import yaml

from app.models.config_models import (
    BusinessConfig,
    DomainsConfig,
    SiteConfig,
    ServiceConfig,
    LimitsConfig,
    ContentConfig,
)

_config_cache: Optional[BusinessConfig] = None


def _load_raw_config() -> dict:
    base_dir = Path(__file__).resolve().parents[1]
    config_path = base_dir / "config" / "business.yml"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_business_config() -> BusinessConfig:
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    raw = _load_raw_config()

    domains = DomainsConfig(**raw["domains"])
    site = SiteConfig(**raw["site"])
    services = [ServiceConfig(**s) for s in raw.get("services", [])]
    limits = LimitsConfig(**raw["limits"])
    content = ContentConfig(**raw["content"])

    cfg = BusinessConfig(
        brand=raw["brand"],
        domains=domains,
        site=site,
        services=services,
        regions=raw.get("regions", []),
        limits=limits,
        content=content,
    )

    _config_cache = cfg
    return cfg
