from backend.helper import retrieve_val_from_env
from openai import OpenAI


def create_opencode_client(max_retries: int = 0, timeout: float = 30.0):
    opencode_api_key = retrieve_val_from_env("OPENCODE_API_KEY", "")
    if not opencode_api_key:
        raise ValueError("Opencode API key missing! No AI model available for inference.")
    
    return OpenAI(
        api_key=opencode_api_key,
        base_url="https://opencode.ai/inference/go/openai/v1",
        default_headers={"User-Agent": "personal-rag/1.0"},
        timeout=timeout,
        max_retries = max_retries
    )

def opencode_send_for_inference(client, *, model, messages, max_output_tokens, session_id):
    response = client.chat.completions.create(
        model=model, 
        messages=messages, 
        max_tokens=max_output_tokens,
        extra_headers={"x-opencode-session": f"ses_{session_id}"}
    )
    
    if not response.choices:
        raise RuntimeError("Error! No valid response.")

    if response.choices[0].finish_reason in ["content_filter", "length"]:
        raise ValueError(f"Error! Response was not complete due to {response.choices[0].finish_reason}")
    
    message = response.choices[0].message
    usage = response.usage
    output = {"provider": "opencode",
              "model": response.model,
              "request_id": response.id, 
              "role": message.role, 
              "content": message.content, 
              "finish_reason": response.choices[0].finish_reason,
              "tool_calls": [
                call.model_dump(mode="json")
                for call in (message.tool_calls or [])
              ], 
              "prompt_tokens": usage.prompt_tokens if usage else None, 
              "completion_tokens": usage.completion_tokens if usage else None,
              "total_tokens": usage.total_tokens if usage else None
              }
    
    return output
