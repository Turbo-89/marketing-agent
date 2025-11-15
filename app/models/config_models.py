from pydantic import BaseModel
from typing import List


class ServiceConfig(BaseModel):
    key: str
    name: str


class LimitsConfig(BaseModel):
    max_new_pages_per_day: int
    require_manual_approve_new_pages: bool = True


class ContentConfig(BaseModel):
    tone: str
    cta: str


class SiteConfig(BaseModel):
    router: str                  # "app" of "pages"
    repo_owner: str
    repo_name: str
    default_branch: str


class DomainsConfig(BaseModel):
    primary: str


class BusinessConfig(BaseModel):
    brand: str
    domains: DomainsConfig
    site: SiteConfig
    services: List[ServiceConfig]
    regions: List[str]
    limits: LimitsConfig
    content: ContentConfig
