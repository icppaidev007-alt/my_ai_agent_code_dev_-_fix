import os
import sys
import subprocess
import glob
import json
from groq import Groq

# ==========================================
# 1. DEFINE CONTROLLED TOOLS (FUNCTIONS)
# ==========================================

def list_directory(path: str) -> str:
    print(f"[Agent Tool] list_directory -> {path}")
    try:
        if not os.path.isdir(path):
            return f"Error: {path} is not a valid directory."
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error: {e}"

def search_files(directory: str, extension: str, pattern: str) -> str:
    print(f"[Agent Tool] search_files -> {pattern} in {extension} files at {directory}")
    results = []
    try:
        search_path = os.path.join(directory, f"**/*{extension}")
        for filepath in glob.glob(search_path, recursive=True):
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern in line:
                                results.append(f"{filepath}:{line_num}: {line.strip()}")
                except UnicodeDecodeError:
                    continue
        return "\n".join(results) if results else "No matches found."
    except Exception as e:
        return f"Error: {e}"

def read_file_lines(path: str, start_line: int, end_line: int) -> str:
    print(f"[Agent Tool] read_file_lines -> {path} (Lines {start_line} to {end_line})")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 1-indexed to 0-indexed
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)
        
        if start_idx >= len(lines):
            return f"Error: start_line {start_line} is beyond the end of the file (Total lines: {len(lines)})."
            
        selected_lines = lines[start_idx:end_idx]
        output = []
        for i, line in enumerate(selected_lines, start=start_idx + 1):
            output.append(f"{i}: {line.rstrip()}")
            
        result_str = "\n".join(output)
        if len(result_str) > 8000:
            return "Error: Requested line range is still too large. Please request a smaller range (e.g. 50 lines)."
        return result_str
    except Exception as e:
        return f"Error: {e}"

def edit_file(path: str, search_string: str, replacement_string: str) -> str:
    print(f"[Agent Tool] edit_file -> Modifying {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if search_string not in content:
            return "Error: search_string not found in file. Ensure exact match."
        new_content = content.replace(search_string, replacement_string)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return "Success: File updated."
    except Exception as e:
        return f"Error: {e}"

def run_build() -> str:
    print(f"[Agent Tool] run_build -> Compiling muparser...")
    try:
        result = subprocess.run(
            ["cmake", "--build", "build", "--config", "Release"],
            cwd=r"D:\Agent Stuff\muparser",
            capture_output=True, text=True
        )
        full_out = result.stdout + "\n" + result.stderr
        # Truncate to last 1500 chars to save tokens
        if len(full_out) > 1500: full_out = "...[TRUNCATED]...\n" + full_out[-1500:]
        return f"Build Exit Code: {result.returncode}\n{full_out}"
    except Exception as e:
        return f"Error: {e}"

def run_tests() -> str:
    print(f"[Agent Tool] run_tests -> Running t_ParserTest.exe...")
    try:
        result = subprocess.run(
            [r".\build\Release\t_ParserTest.exe"],
            cwd=r"D:\Agent Stuff\muparser",
            capture_output=True, text=True
        )
        full_out = result.stdout + "\n" + result.stderr
        # Truncate to last 2000 chars to save tokens (usually contains the failure summary)
        if len(full_out) > 2000: full_out = "...[TRUNCATED]...\n" + full_out[-2000:]
        return f"Tests Exit Code: {result.returncode}\n{full_out}"
    except Exception as e:
        return f"Error: {e}"

# ==========================================
# 2. MAIN ORCHESTRATION LOOP (GROQ)
# ==========================================

tools = [
    {"type": "function", "function": {"name": "list_directory", "description": "Lists contents of a directory.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute path to directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "search_files", "description": "Searches for a literal text string (NOT regular expression).", "parameters": {"type": "object", "properties": {"directory": {"type": "string", "description": "Absolute path"}, "extension": {"type": "string", "description": "File extension e.g. .cpp"}, "pattern": {"type": "string", "description": "Literal text to search"}}, "required": ["directory", "extension", "pattern"]}}},
    {"type": "function", "function": {"name": "read_file_lines", "description": "Reads specific lines of a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start_line": {"type": "integer"}, "end_line": {"type": "integer"}}, "required": ["path", "start_line", "end_line"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replaces exact search_string with replacement_string.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "search_string": {"type": "string"}, "replacement_string": {"type": "string"}}, "required": ["path", "search_string", "replacement_string"]}}},
    {"type": "function", "function": {"name": "run_build", "description": "Compiles muparser.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "run_tests", "description": "Runs test executable.", "parameters": {"type": "object", "properties": {}}}}
]

tools_dict = {
    "list_directory": list_directory, "search_files": search_files,
    "read_file_lines": read_file_lines, "edit_file": edit_file,
    "run_build": run_build, "run_tests": run_tests
}

import re
import time

def parse_retry_after(error_str):
    m = re.search(r'try again in (?:(\d+)m)?(?:([\d\.]+)s)?', error_str)
    if m:
        mins = int(m.group(1)) if m.group(1) else 0
        secs = float(m.group(2)) if m.group(2) else 0
        return int(mins * 60 + secs)
    return None

def send_with_model_rotation(client, models_list, messages, tools):
    fallback_delay = 20
    current_idx = getattr(send_with_model_rotation, "current_idx", 0)
    retries = 0
    max_retries = 5
    
    while retries < max_retries:
        model = models_list[current_idx]
        try:
            res = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.0
            )
            send_with_model_rotation.current_idx = current_idx
            return res
        except Exception as e:
            err_str = str(e)
            retries += 1
            if "429" in err_str or "limit" in err_str.lower() or "529" in err_str:
                print(f"\n[Model Switch] '{model}' hit a limit! (Attempt {retries}/{max_retries}). Rotating...")
                current_idx = (current_idx + 1) % len(models_list)
                
                if current_idx == getattr(send_with_model_rotation, "current_idx", 0):
                    print(f"\n[Rate Limit] All models exhausted in this cycle. Pausing {fallback_delay}s...")
                    time.sleep(fallback_delay)
                    fallback_delay = min(fallback_delay * 2, 300)
                continue
            
            # If it's a syntax or other API error, don't loop infinitely
            print(f"\n[Error] Unhandled API error: {err_str[:100]}...")
            if retries >= max_retries:
                raise e
            continue
            
    raise Exception(f"Failed after {max_retries} attempts.")

send_with_model_rotation.current_idx = 0

import openai
import winreg

def get_api_key():
    key = os.environ.get("MISTRAL_API_KEY")
    if key: return key
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as rkey:
            key, _ = winreg.QueryValueEx(rkey, "MISTRAL_API_KEY")
            return key
    except WindowsError:
        pass
    return None

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    api_key = get_api_key()
    if not api_key:
        print("ERROR: MISTRAL_API_KEY environment variable not set.")
        sys.exit(1)

    ticket_path = r"D:\Agent Stuff\AG Discussion Files\Ticket-842.txt"
    if not os.path.exists(ticket_path):
        print(f"ERROR: Could not find {ticket_path}")
        sys.exit(1)
        
    with open(ticket_path, "r", encoding="utf-8") as f:
        ticket_content = f.read()

    # Initialize OpenAI client with Mistral API base URL
    client = openai.OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_key
    )
    
    # Models array for Mistral (auto-rotates if one hits a limit)
    mistral_models = [
        "mistral-small-latest",
        "open-mistral-nemo",
        "open-mixtral-8x7b"
    ]
    
    system_instruction = (
        "You are an autonomous C++ debugging agent. "
        "Your target repository is located at D:\\Agent Stuff\\muparser. "
        "You must follow this exact loop until the issue is solved:\n"
        "1. Read the user's ticket.\n"
        "2. Investigate the codebase using list_directory, search_files, and read_file_lines.\n"
        "3. Identify the root cause and modify the code using edit_file.\n"
        "4. Run run_build() and then run_tests().\n"
        "5. If tests fail, investigate the failure and iterate.\n"
        "6. Once fixed and tests pass, explain your fix clearly to the user."
    )
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Please fix the following ticket:\n\n{ticket_content}"}
    ]
    
    print("\n==============================================")
    print("🤖 MISTRAL AI AUTONOMOUS DEBUGGING AGENT STARTED")
    print("==============================================")
    print("Agent is now thinking and executing tools...\n")
    
    step_count = 0
    
    try:
        # Clear the old log file at startup
        log_dir = r"D:\Agent Stuff\logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_path = os.path.join(log_dir, "agent_live_log.txt")
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write("🤖 AGENT LIVE LOGGING STARTED\n================================\n")
            
        while True:
            step_count += 1
            
            response = send_with_model_rotation(
                client=client,
                models_list=mistral_models,
                messages=messages,
                tools=tools
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # --- Live Log: Agent's Thought ---
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"\n\n--- STEP {step_count} ---\n")
                if response_message.content:
                    lf.write(f"🤔 THOUGHT:\n{response_message.content}\n")
            
            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    if func_args is None:
                        func_args = {}
                    
                    if func_name in tools_dict:
                        result_str = tools_dict[func_name](**func_args)
                    else:
                        result_str = f"Error: Tool {func_name} not found"
                        
                    # --- Live Log: Tool execution and result ---
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(f"\n🛠️ TOOL CALLED: {func_name}\n")
                        lf.write(f"ARGS: {json.dumps(func_args, indent=2)}\n")
                        # We truncate result to 1000 chars in log to avoid massive files
                        res_preview = str(result_str)
                        if len(res_preview) > 1000:
                            res_preview = res_preview[:1000] + "\n...[TRUNCATED IN LOG]..."
                        lf.write(f"RESULT:\n{res_preview}\n")
                        
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": str(result_str),
                    })
            else:
                print("\n==============================================")
                print("🎉 AGENT FINAL REPORT")
                print("==============================================")
                print(response_message.content)
                
                # Save the report to a file so it doesn't get lost
                report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_fix_report.txt")
                with open(report_path, "w", encoding="utf-8") as rf:
                    rf.write("AGENT FINAL FIX REPORT\n========================\n\n")
                    rf.write(response_message.content)
                print(f"\n[Info] Full explanation saved to: {report_path}")
                break
                
    except Exception as e:
        print(f"\n❌ Agent Loop Terminated Error: {e}")

if __name__ == "__main__":
    main()
