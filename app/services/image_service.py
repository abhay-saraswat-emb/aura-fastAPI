import os
from openai import OpenAI
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Union, AsyncGenerator, Any
from google import genai
from google.genai import types
from typing import List, Dict, Optional
import httpx


load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def generate_response(
    model: str, 
    prompt: str, 
    system_prompt: str = "You are a helpful assistant.", 
    max_tokens: int = 256, 
    temperature: float = 0.7,
) -> str:
    """
    Generate chatbot response with a image.
    
    Args:
        model: The model to use (e.g., "Claude", "GPT-4")
        prompt: The user's input prompt
        system_prompt: Instructions for the AI
        max_tokens: Maximum response length
        temperature: Randomness of response (0-1)
        
    Returns:
        A complete string response
    """

    if model == "Claude":
        # Non-streaming Claude response
        response = claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            system= system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.content
    else:
        # Your existing code for other models
        pass

async def image_claude_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    image_url:str = None
):
    """
    Stream a response from Claude model for image.
    
    Args:
        prompt: The user's input prompt
        system_prompt: Instructions for the AI
        max_tokens: Maximum response length
        temperature: Randomness of response (0-1)
        conversation_history: history of conversatio
        image_url: url of image
        
    Yields:
        Chunks of the generated response
    """
    try:
        # Convert conversation history to Claude format
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        user_message = []
        
        # If a image URL is provided, include it in the user message
        if image_url:
            user_message.append({
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_url
                }
            })
        
        # Add the user's text prompt
        user_message.append({
            "type": "text",
            "text": prompt
        })
        
        messages.append({"role": "user", "content": user_message})


        with claude_client.messages.stream(
            model="claude-3-7-sonnet-20250219",
            system=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        ) as stream:
            for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"


async def image_genai_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    image_url: str = None
):
    try:
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
            contents = [current_content]
        
        # Handle image if URL is provided
        if image_url:
            try:
                doc_data = httpx.get(image_url).content  # Retrieve image bytes
                image_part = types.Part.from_bytes(
                    data=doc_data,
                    mime_type='image/jpeg',
                )
                contents.insert(0, image_part)  # Add image as the first input
            except Exception as e:
                yield f"data: Error fetching image: {str(e)}\n\n"
        
        stream = genai_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=temperature
            ),
        )

        for chunk in stream:
            yield f"{chunk.text}"
            
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"


async def image_openai_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    image_url:str = None
):
    try:        
        # Handle image if URL is provided
        if image_url:
        
            user_content = []
            user_content.append({"type": "input_image", "image_url": image_url})
            
            # Append conversation history
            input_data = []
            # for msg in conversation_history:
            #     role = msg["role"]
            #     content = [{"type": "input_text", "text": msg["content"]}]
            #     input_data.append({"role": role, "content": content})
            
            # Add the current user message
            user_content.append({"type": "input_text", "text": prompt})
            input_data.append({"role": "user", "content": user_content})
            
            # Ensure image attachment if available
            stream =openai_client.responses.create(
                model="gpt-4o",
                input=input_data,
                temperature=temperature, 
                instructions=system_prompt, 
                # max_tokens=max_tokens, 
                stream=True,
            )
            
            for chunk in stream:
                if hasattr(chunk, "delta"):
                    yield (chunk.delta)
            
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"
