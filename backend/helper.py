from dotenv import load_dotenv
import os
from typing import TypeVar

load_dotenv()
T = TypeVar("T")

def retrieve_val_from_env(env_name: str, default_val: T) -> T:
    raw_val = os.getenv(env_name)
    
    if not raw_val:
        return default_val
    
    default_type = type(default_val)
    
    if default_type is bool:
        return raw_val.strip().lower() in ("true", "1", "yes", "on")
    try:
        return default_type(raw_val)
    except (ValueError, TypeError):
        return default_val
    