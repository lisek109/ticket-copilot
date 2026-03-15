import os
from typing import List, Dict, Any
from app.llm.client import get_client

def synthesize_answer(ticket_text: str, sources: List[Dict[str, Any]]) -> str | None:
    """
    Create a concise, professional reply using retrieved sources.
    Returns None if LLM is not configured.
    """
    client = get_client()
    if client is None:
        return None

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    if not deployment:
        return None

    api_version = getattr(client, "_azure_api_version", "2024-02-15-preview")

    # Build context with citations
    context_lines = []
    for i, s in enumerate(sources, start=1):
        src = s.get("source", "unknown")
        snip = (s.get("snippet") or "")[:300]
        context_lines.append(f"[{i}] {src}: {snip}")
    context = "\n".join(context_lines)

    system = (
        "You are an IT support copilot. "
        "Draft a professional email reply to the sender of the ticket. "
        "If the ticket contains a line like 'Sender name: X', use that sender name in the greeting. "
        "Do not use the agent's or ticket owner's name as the greeting target. "
        "Use only the provided knowledge base snippets as grounding. "
        "If information is missing, ask only for the minimum required details. "
        "Keep the reply concise and actionable. "
        "Always include citations like [1], [2] when referencing KB sources."
    )

    user = (
        f"Ticket:\n{ticket_text}\n\n"
        f"Internal procedure snippets:\n{context}\n\n"
        "Write the suggested reply."
    )

    # Chat Completions style call via SDK base_url + deployments.
    # Note: Azure requires api-version query parameter.
    resp = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=350,
        
    )

    return resp.choices[0].message.content.strip()
