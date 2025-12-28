"""
Helper script to check if Gemini API key is configured correctly.
"""
import os
import sys

def check_api_key():
    """Check API key configuration."""
    print("Checking Gemini API key configuration...")
    print("-" * 50)
    
    # Check if .env file exists
    env_path = ".env"
    if not os.path.exists(env_path):
        print("[ERROR] .env file not found!")
        print(f"   Expected location: {os.path.abspath(env_path)}")
        print("\n[INFO] Solution:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: GEMINI_API_KEY=your_api_key_here")
        print("   3. Get your API key from: https://makersuite.google.com/app/apikey")
        return False
    
        print("[OK] .env file found")
    
    # Try to load settings
    try:
        from app.config.settings import settings
        
        api_key = settings.gemini_api_key
        
        if not api_key:
            print("[ERROR] GEMINI_API_KEY is empty in .env file")
            return False
        
        if "your_gemini_api_key" in api_key.lower() or "your_" in api_key.lower():
            print("[ERROR] GEMINI_API_KEY appears to be a placeholder")
            print(f"   Current value: {api_key[:20]}...")
            print("\n[INFO] Solution: Replace with your actual API key")
            return False
        
        if len(api_key.strip()) < 20:
            print("[ERROR] GEMINI_API_KEY appears to be invalid (too short)")
            print(f"   Length: {len(api_key)} characters")
            return False
        
        print(f"[OK] API key found (length: {len(api_key)} characters)")
        print(f"   Key preview: {api_key[:10]}...{api_key[-5:]}")
        
        # Try to initialize embeddings to validate the key
        print("\nTesting API key with Gemini...")
        try:
            from app.rag.embeddings import GeminiEmbeddings
            embeddings = GeminiEmbeddings()
            print("[OK] API key is valid and working!")
            return True
        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg or "API_KEY" in error_msg or "invalid" in error_msg.lower():
                print("[ERROR] API key is invalid or not authorized")
                print(f"   Error: {error_msg}")
                print("\n[INFO] Solution:")
                print("   1. Verify your API key at: https://makersuite.google.com/app/apikey")
                print("   2. Make sure the key is correctly copied (no extra spaces)")
                print("   3. Check if the API key has the necessary permissions")
                return False
            else:
                print(f"[WARNING] Could not validate API key: {e}")
                print("   The key format looks correct, but validation failed")
                return False
        
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error loading settings: {e}")
        print("\n[INFO] Make sure:")
        print("   1. .env file is in the project root")
        print("   2. .env file contains: GEMINI_API_KEY=your_key")
        print("   3. No quotes around the API key value")
        return False


if __name__ == "__main__":
    success = check_api_key()
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] All checks passed! You're ready to use the RAG chatbot.")
        sys.exit(0)
    else:
        print("[FAILED] API key configuration needs to be fixed.")
        sys.exit(1)

