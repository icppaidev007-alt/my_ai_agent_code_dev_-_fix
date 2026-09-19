import os
import sys
import winreg

def get_api_key():
    # 1. Check current environment variables
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
        
    # 2. Check registry because setx does not update the current process env vars automatically
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as registry_key:
            key, _ = winreg.QueryValueEx(registry_key, "GEMINI_API_KEY")
            return key
    except WindowsError:
        pass
    
    return None

def main():
    key = get_api_key()
    if not key:
        print("FAIL: No GEMINI_API_KEY found in environment or registry.")
        sys.exit(1)
        
    print("API Key found locally. Attempting to initialize google-genai client...")
    
    # Temporarily set it in os.environ so the SDK can pick it up automatically
    os.environ["GEMINI_API_KEY"] = key
    
    try:
        from google import genai
        client = genai.Client()
        print("Sending test request to gemini-3.6-flash...")
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents='Hello, this is a connectivity test. Please reply ONLY with the exact words: "API IS WORKING"'
        )
        print("\n--- RESPONSE FROM GEMINI ---")
        print(response.text.strip())
        print("----------------------------\n")
        print("SUCCESS: API key is valid and working!")
    except Exception as e:
        print(f"\nERROR: API call failed.\nDetails: {e}")

if __name__ == "__main__":
    main()
