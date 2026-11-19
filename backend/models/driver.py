from openai import OpenAI, APIConnectionError, APIStatusError
from backend.models.opencode import (
    create_opencode_client, 
    opencode_send_for_inference,
    )
from backend.helper import retrieve_val_from_env
import time

providers = {}
providers["opencode"] = {"create_client": create_opencode_client, "send": opencode_send_for_inference, "model" : retrieve_val_from_env("OPENCODE_MODEL", "deepseek-v4.1-flash")} 
# other clients

clients = {}

def call_llm(messages: list[dict], max_output_tokens, session_id):
    latest_error= None
    
    for provider_name, config_info in providers.items():
        try:
            client = get_client(provider_name)
            return config_info["send"](
                client=client,
                model=config_info["model"],
                messages=messages,
                max_output_tokens=max_output_tokens,
                session_id=session_id
            )
        
        except APIConnectionError as e:
            latest_error = e
        except APIStatusError as e:
            if e.status_code != 429 and e.status_code < 500: # only ratelimiting or server failures
                raise
            latest_error = e
            
    raise RuntimeError("No provider returned a successful response") from latest_error

def get_client(provider_name):
    if provider_name not in clients:    
        factory = providers[provider_name]["create_client"]
        clients[provider_name] = factory()
        
    return clients[provider_name]

