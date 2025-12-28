"""
Helper script to migrate .env file from Gemini to Groq.
"""
import os
import re
import sys

def safe_print(text):
    """Print with safe encoding for Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emojis for Windows console
        text_clean = text.encode('ascii', 'ignore').decode('ascii')
        print(text_clean)

def migrate_env_file():
    """Migrate .env file from Gemini to Groq configuration."""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        safe_print("[ERROR] .env file not found!")
        return
    
    # Read current .env file
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    safe_print("[INFO] Current .env file content:")
    safe_print("-" * 50)
    print(content)
    safe_print("-" * 50)
    print()
    
    # Check if it needs migration
    needs_migration = False
    has_gemini = "GEMINI_API_KEY" in content or "gemini" in content.lower()
    has_groq = "GROQ_API_KEY" in content
    
    if has_gemini and not has_groq:
        needs_migration = True
        safe_print("[WARNING] Found Gemini API key configuration. Migration needed.")
    elif has_groq:
        safe_print("[SUCCESS] Already using Groq API key!")
        return
    else:
        safe_print("[WARNING] No API key found. You'll need to add GROQ_API_KEY.")
    
    if needs_migration:
        # Extract Gemini API key if present
        gemini_match = re.search(r'GEMINI_API_KEY\s*=\s*(.+)', content, re.IGNORECASE)
        if gemini_match:
            gemini_key = gemini_match.group(1).strip()
            safe_print(f"\n[INFO] Found Gemini API key (length: {len(gemini_key)})")
            safe_print("[WARNING] Note: You'll need to get a new Groq API key from https://console.groq.com/keys")
            print()
        
        # Create backup
        backup_path = ".env.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        safe_print(f"[INFO] Backup created: {backup_path}")
        
        # Replace Gemini references with Groq
        new_content = content
        
        # Replace GEMINI_API_KEY with GROQ_API_KEY (but keep placeholder)
        new_content = re.sub(
            r'GEMINI_API_KEY\s*=\s*.+',
            'GROQ_API_KEY=your_groq_api_key_here',
            new_content,
            flags=re.IGNORECASE
        )
        
        # Remove old Gemini model settings
        new_content = re.sub(r'GEMINI_MODEL\s*=\s*.+\n?', '', new_content, flags=re.IGNORECASE)
        new_content = re.sub(r'GEMINI_EMBEDDING_MODEL\s*=\s*.+\n?', '', new_content, flags=re.IGNORECASE)
        
        # Add Groq model if not present
        if 'GROQ_MODEL' not in new_content:
            new_content += "\n# Groq Model (optional)\n# GROQ_MODEL=llama-3.1-70b-versatile\n"
        
        # Add embedding model info
        if 'EMBEDDING_MODEL' not in new_content:
            new_content += "\n# Local Embeddings (free, no API key needed)\n# EMBEDDING_MODEL=all-MiniLM-L6-v2\n"
        
        # Write new content
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        safe_print("[SUCCESS] .env file migrated!")
        print()
        safe_print("[INFO] Updated .env file:")
        safe_print("-" * 50)
        print(new_content)
        safe_print("-" * 50)
        print()
        safe_print("[WARNING] IMPORTANT: Update GROQ_API_KEY with your actual Groq API key!")
        safe_print("   Get it from: https://console.groq.com/keys")
    else:
        # Just show what they need
        safe_print("\n[INFO] Your .env file should contain:")
        safe_print("-" * 50)
        print("GROQ_API_KEY=your_groq_api_key_here")
        print()
        print("# Optional settings:")
        print("# GROQ_MODEL=llama-3.1-70b-versatile")
        print("# EMBEDDING_MODEL=all-MiniLM-L6-v2")
        safe_print("-" * 50)

if __name__ == "__main__":
    migrate_env_file()

