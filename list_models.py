import os
import winreg
from google import genai

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(registry_key, "GEMINI_API_KEY")
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        pass
    return None

api_key = get_api_key()
os.environ["GEMINI_API_KEY"] = api_key
client = genai.Client()

print("Available Models:")
for m in client.models.list():
    print(m.name)
