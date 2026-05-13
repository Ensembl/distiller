import os
import json
from functools import lru_cache

from pydantic import BaseModel, ValidationError

class Dataset(BaseModel):
    label:str
    id:str
    path:str

class Config(BaseModel):
    datasets: list[Dataset]

class ConfigError(RuntimeError):
    """Raised when application settings are invalid or missing."""
    pass

@lru_cache(maxsize=1)
def get_config(override_config_path = None) -> Config:
    # try to load json from either a env path or from root
    config_file= os.getenv("DISTILLER_CONFIG","config.json")
    if override_config_path:
        config_file = override_config_path
    
    try:
        with open(config_file) as config_stream:
            config_details = json.load(config_stream)
            print(config_details)
            return Config.model_validate(config_details)
    except OSError as e:
        raise ConfigError("Unable to load config")
    except ValidationError as ve:
        raise ConfigError("Validation error")

def get_dataset_path(id:str) -> str | None:
    config = get_config()
    
    for c in config.datasets:
        if c.id == id:
            return c.path
    return None
            