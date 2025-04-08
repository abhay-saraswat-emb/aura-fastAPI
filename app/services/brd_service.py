import os
from typing import List, Dict
import anthropic
from dotenv import dotenv_values
import json


# Load custom prompts from .env.prompts file
prompts = dotenv_values(".env.prompts")

async def brd_generator(
    max_tokens: int, 
    temperature: float = 1,
    conversation_history: List[Dict[str, str]] = [],
    phase: int = 1
):
    try:
        # Get the correct system prompt for the given phase
        system_prompt = prompts.get("PHASE1") + prompts.get("PHASE2") + prompts.get("PHASE3") + prompts.get("PHASE4")


        # Format messages for Claude API
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        # messages.append({"role": "user", "content": system_prompt })

        # Set up Claude API parameters
        api_params = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "system": system_prompt,
            "betas": ["output-128k-2025-02-19"],
            "thinking": {
                "type": "enabled",
                "budget_tokens": 6000
            }
        }

        # Claude client using your API key
        claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Stream the response
        # Stream the response
        with claude_client.beta.messages.stream(**api_params) as stream:
            for text in stream.text_stream:
                # Format each chunk of text with the "0:" prefix
                yield f'0:"{text.replace("\"", "\\\"").replace("\n", "\\n")}"\n'
                
    except Exception as e:
        error_msg = str(e)
        yield f'0:"Error: {error_msg.replace("\"", "\\\"").replace("\n", "\\n")}"\n'
        yield f'e:{{"finishReason":"error"}}\n'
        yield f'd:{{"finishReason":"error"}}\n'