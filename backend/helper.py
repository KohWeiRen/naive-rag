from dotenv import load_dotenv
import os
from typing import TypeVar
from pathlib import Path

T = TypeVar("T")

def retrieve_val_from_env(env_name: str, default_val: T, path: Path = Path(__file__).resolve().parent / ".env") -> T:
    # if not path.exists:
    #     raise f".env file at path: {path} does not exist! Unable to access secrets"
    
    try:
        load_dotenv(path)
    except Exception:
        print(f".env file at path: {path} does not exist! Unable to access secrets")
    
    raw_val = os.getenv(env_name, "")
    
    if not raw_val:
        return default_val
    
    default_type = type(default_val)
    
    if default_type is bool:
        return raw_val.strip().lower() in ("true", "1", "yes", "on")
    try:
        return default_type(raw_val)
    except (ValueError, TypeError):
        return default_val
    