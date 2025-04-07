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
import pandas as pd
import requests
from io import BytesIO


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
    Generate chatbot response with a excel.
    
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

async def excel_claude_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    excel_url:str = None
):
    """
    Stream a response from Claude model for excel.
    
    Args:
        prompt: The user's input prompt
        system_prompt: Instructions for the AI
        max_tokens: Maximum response length
        temperature: Randomness of response (0-1)
        conversation_history: history of conversatio
        excel_url: url of excel
        
    Yields:
        Chunks of the generated response
    """
    try:
        # Convert conversation history to Claude format
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
        user_message_content = []

        # If Excel URL is provided, download and parse it
        if excel_url:
            try:
                response = requests.get(excel_url)
                response.raise_for_status()

                # Read Excel content using pandas
                excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)

                # Convert each sheet to text
                excel_text = ""
                for sheet_name, df in excel_data.items():
                    excel_text += f"\n\nSheet: {sheet_name}\n"
                    excel_text += df.to_string(index=False)

                # Add parsed Excel content as context
                user_message_content.append({
                    "type": "text",
                    "text": f"Here is the content of the Excel file:\n{excel_text}"
                })

            except Exception as ex:
                yield f"data: Error reading Excel file: {str(ex)}\n\n"
                return

        # Add the user's actual prompt
        user_message_content.append({
            "type": "text",
            "text": prompt
        })

        # Append user's message to messages
        messages.append({"role": "user", "content": user_message_content})

        # Stream response from Claude
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


async def excel_genai_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    excel_url: str = None
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

        # Initialize user message parts
        user_parts = []

        # If Excel URL is provided, parse it and convert to text
        if excel_url:
            try:
                response = httpx.get(excel_url)
                response.raise_for_status()

                # Read Excel file using pandas
                excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)

                # Convert Excel sheets to text
                excel_text = ""
                for sheet_name, df in excel_data.items():
                    excel_text += f"\n\nSheet: {sheet_name}\n"
                    excel_text += df.to_string(index=False)

                # Add parsed Excel content as context
                user_parts.append(types.Part(text=f"Here is the content of the Excel file:\n{excel_text}"))

            except Exception as e:
                yield f"data: Error reading Excel file: {str(e)}\n\n"
                return

        # Add the main user prompt
        user_parts.append(types.Part(text=prompt))

        # Construct the current content message
        current_content = types.Content(
            role="user",
            parts=user_parts
        )

        # Combine conversation history and current message
        contents = history_content + [current_content]

        # Stream response from Gemini
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

async def excel_openai_stream_response(
    prompt: str, 
    system_prompt: str, 
    max_tokens: int, 
    temperature: float,
    conversation_history: List[Dict[str, str]] = [],
    excel_url: str = None
):
    try:
        input_data = []

        # Add conversation history
        for msg in conversation_history:
            role = msg["role"]
            content = [{"type": "input_text", "text": msg["content"]}]
            input_data.append({"role": role, "content": content})

        # Prepare user's message
        user_content = []

        # If Excel URL is provided, parse it and convert to text
        if excel_url:
            try:
                response = httpx.get(excel_url)
                response.raise_for_status()

                # Load Excel file using pandas
                excel_data = pd.read_excel(BytesIO(response.content), sheet_name=None)

                # Convert Excel to readable string format
                excel_text = ""
                for sheet_name, df in excel_data.items():
                    excel_text += f"\n\nSheet: {sheet_name}\n"
                    excel_text += df.to_string(index=False)

                # Add Excel text to the prompt
                user_content.append({
                    "type": "input_text",
                    "text": f"Here is the content of the Excel file:\n{excel_text}"
                })

            except Exception as ex:
                yield f"data: Error reading Excel file: {str(ex)}\n\n"
                return

        # Append the main prompt
        user_content.append({
            "type": "input_text",
            "text": prompt
        })

        # Final user message
        input_data.append({
            "role": "user",
            "content": user_content
        })

        # Call OpenAI API with streaming
        stream = openai_client.responses.create(
            model="gpt-4o",
            input=input_data,
            temperature=temperature, 
            instructions=system_prompt,
            # max_tokens=max_tokens,  # Uncomment if supported by your OpenAI setup
            stream=True,
        )

        for chunk in stream:
            if hasattr(chunk, "delta"):
                yield chunk.delta

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"