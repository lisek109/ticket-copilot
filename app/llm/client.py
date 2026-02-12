import os
from openai import OpenAI

def get_client() -> OpenAI | None:
    """
    Returns an OpenAI client configured for Azure OpenAI.
    If env vars are missing, returns None (so we can fallback).
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not endpoint or not api_key:
        return None

    # Azure OpenAI uses a custom base_url; api-version is passed via query.
    
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # For OpenAI SDK, Azure is typically configured via base_url.
    base_url = f"{endpoint}/openai/deployments"

    # store api_version on the client via default query parameter in requests,
    # by appending it later per request (see call below).
    client = OpenAI(api_key=api_key, base_url=base_url)
    client._azure_api_version = api_version  # simple attribute for later
    return client
