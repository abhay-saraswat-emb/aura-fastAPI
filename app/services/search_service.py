import os
from openai import OpenAI
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Union, AsyncGenerator, Any
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from google.genai.types import Tool, GoogleSearch
from .tavily_tool import tavily_search


load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

google_search_tool = Tool(
    google_search = GoogleSearch()
)


async def claude_perform_search(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = []
):
    """
    Stream a response from Claude model for internet search.
    
    Args:
        prompt: The user's input prompt
        system_prompt: Instructions for the AI
        max_tokens: Maximum response length
        temperature: Randomness of response (0-1)
        
    Yields:
        Chunks of the generated response
    """
    try:
        print("claude-internet-search")
        # Convert conversation history to Claude format
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        response =  claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            tools=[
                {
                    "name": "tavily_search",
                    "description": "Search the web for up-to-date information",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for the internet"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ],
            tool_choice={"type": "auto"},
            system=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        ) 

        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_call = content_block
                messages.append({
                    "role": "assistant",
                    "content": [  # This is a list of content blocks
                        {
                            "type": "tool_use",
                            "id": tool_call.id,
                            "name": tool_call.name,
                            "input": tool_call.input
                        }
                    ]
                })

                # Step 2: Call the tool function (like Tavily)
                tool_response = tavily_search(tool_call.input["query"])

                # Step 3: Add the tool_result from user
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": [
                                {
                                    "type": "text",
                                    "text": tool_response
                                }
                            ]
                        }
                    ]
                })

                # Step 4: Add empty assistant message so Claude will continue
                messages.append({
                    "role": "assistant",
                    "content": []
                })

                # Send tool response back to Claude
                with claude_client.messages.stream(
                    model="claude-3-7-sonnet-20250219",
                    system=system_prompt,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )  as stream:
                    for chunk in stream.text_stream:
                        yield chunk
                return
            
        for block in response.content:
            if block.type == "text":
                yield block.text

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"


async def gemini_perform_search(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = []
):
    try:
        print("gemini-internet-search")
        # Format the conversation history for Gemini
        history_content = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            history_content.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))
        
        # Add current prompt
        current_content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        
        if history_content:
            # Add history and current prompt
            contents = history_content + [current_content]
        else:
            # Just the current prompt if no history
            contents = current_content
        
        stream = genai_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
                tools=[google_search_tool],
                response_modalities=["TEXT"],
            ),
        )

        for chunk in stream:
            yield f"{chunk.text}"
            
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"


async def gpt_perform_search(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = []
):
    try:
        print("gpt-internet-search")
        # Prepare messages with history
        messages = []
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        stream = openai_client.responses.create(
            model="gpt-4o",
            tools=[{ "type": "web_search_preview" }],
            input=messages,
            instructions=system_prompt,
            # temperature=temperature,  
            # max_tokens=max_tokens, 
            stream=True,
        )

        for chunk in stream:
            if hasattr(chunk, "delta"):
                yield (chunk.delta)

            
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"
