import os
import winreg
from google import genai
import time

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key: return key
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(registry_key, "GEMINI_API_KEY")
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        pass
    return None

os.environ["GEMINI_API_KEY"] = get_api_key()
client = genai.Client()

models_to_test = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest"
]

print("Testing models for rate limits...")
working_model = None

for model_name in models_to_test:
    print(f"\n--- Testing {model_name} ---")
    try:
        chat = client.chats.create(model=model_name)
        # Send 22 requests to breach the 20-request daily limit of 3.6-flash
        success = True
        for i in range(22):
            try:
                chat.send_message("hi")
                print(f".", end="", flush=True)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"\n[FAIL] {model_name} hit rate limit at request {i+1}")
                    success = False
                    break
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    print(f"\n[FAIL] {model_name} is deprecated/not found for this key.")
                    success = False
                    break
                else:
                    print(f"\n[ERROR] {model_name} unexpected error: {e}")
                    success = False
                    break
        if success:
            print(f"\n[SUCCESS] {model_name} survived 22 requests! It has a higher quota.")
            working_model = model_name
            break
    except Exception as e:
        print(f"\n[FAIL] {model_name} init error: {e}")

print(f"\n\nFINAL RECOMMENDATION: {working_model}")
