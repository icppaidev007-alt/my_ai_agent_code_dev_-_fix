import os
import sys
import winreg
from google import genai
from google.genai import types

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key: return key
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as rkey:
            key, _ = winreg.QueryValueEx(rkey, "GEMINI_API_KEY")
            return key
    except WindowsError:
        pass
    return None

def list_directory(path: str) -> str:
    """Lists the contents of a directory.
    Args:
        path: Absolute path to the directory (e.g. D:\\Agent Stuff\\muparser)
    """
    print(f"[Agent Tool] list_directory -> {path}")
    try:
        if not os.path.isdir(path):
            return f"Error: {path} is not a valid directory."
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error: {e}"

def read_file(path: str) -> str:
    """Reads the entire content of a file.
    Args:
        path: Absolute path to the file.
    """
    print(f"[Agent Tool] read_file -> {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # For the smoke test, truncate long files
            content = f.read()
            if len(content) > 1000:
                return content[:1000] + "\n...[TRUNCATED]"
            return content
    except Exception as e:
        return f"Error: {e}"

import time

def send_with_retry(chat, message, max_retries=5):
    delay = 10
    for attempt in range(max_retries):
        try:
            return chat.send_message(message)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    print(f"\n[Rate Limit] Gemini rate limit reached. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            raise e

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    api_key = get_api_key()
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found.")
        sys.exit(1)
    os.environ["GEMINI_API_KEY"] = api_key

    client = genai.Client()
    
    tools_list = [list_directory, read_file]
    tools_dict = {t.__name__: t for t in tools_list}
    
    # Disable automatic function calling to manage the loop manually with retries
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a READ-ONLY test agent. "
            "You must investigate D:\\Agent Stuff\\muparser and tell me:\n"
            "- its top-level directories/files\n"
            "- what build system it uses\n"
            "- what executable targets you know about.\n"
            "You are ONLY allowed to use list_directory and read_file. DO NOT MODIFY ANYTHING."
        ),
        temperature=0.0,
        tools=tools_list,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )
    
    chat = client.chats.create(
        model="gemini-3.6-flash", 
        config=config
    )
    
    print("Agent is now thinking and executing tools...\n")
    try:
        response = send_with_retry(chat, 
            "Inspect the muparser repository and tell me:\n"
            "- its top-level directories/files\n"
            "- what build system it uses\n"
            "- what executable targets you know about.\n"
            "Do not modify anything."
        )
        
        while response.function_calls:
            parts = []
            for call in response.function_calls:
                func_name = call.name
                func_args = call.args
                if func_name in tools_dict:
                    result_str = tools_dict[func_name](**func_args)
                else:
                    result_str = f"Error: {func_name} not found."
                    
                parts.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": result_str}
                    )
                )
            
            # Send the tool execution results back to the model
            response = send_with_retry(chat, parts)
            
        print("\n--- AGENT FINAL RESPONSE ---")
        print(response.text)
        
    except Exception as e:
        print(f"\n❌ Agent Error: {e}")

if __name__ == "__main__":
    main()
