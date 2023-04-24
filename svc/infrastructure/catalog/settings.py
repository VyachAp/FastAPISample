from pydantic import BaseSettings


class CatalogClientSettings(BaseSettings):
    class Config:
        env_prefix = "services_catalog_"

    url: str
    timeout_seconds: int = 60
