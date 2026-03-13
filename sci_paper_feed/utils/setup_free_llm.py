"""Interactive setup script for free LLM providers."""

import os
import webbrowser


def create_env_file():
    """Create .env file with user's choice of LLM provider."""
    print("🚀 Welcome to AI Research Paper Feed Setup!")
    print("Let's configure a free LLM provider for testing.\n")
    
    print("Available FREE options:")
    print("1. 🤗 Hugging Face (Recommended for beginners)")
    print("   - Completely free with rate limits")
    print("   - Optional free token for higher limits")
    print("   - Good quality for testing")
    
    print("\n2. 🧠 Google Gemini (Best free option)")
    print("   - High quality (comparable to GPT-4)")
    print("   - Generous free tier (15 requests/minute)")
    print("   - Requires free API key")
    
    print("\n3. 💰 OpenAI (Paid option)")
    print("   - Best quality but costs money")
    print("   - ~$0.01-0.02 per analysis session")
    
    while True:
        choice = input("\nChoose your provider (1-3): ").strip()
        
        if choice == "1":
            setup_huggingface()
            break
        elif choice == "2":
            setup_gemini()
            break
        elif choice == "3":
            setup_openai()
            break
        else:
            print("Please enter 1, 2, or 3")

def setup_huggingface():
    """Setup Hugging Face provider."""
    print("\n🤗 Setting up Hugging Face...")
    print("You can use Hugging Face in two ways:")
    print("1. Without API key (rate limited but free)")
    print("2. With free API token (higher limits)")
    
    use_token = input("\nDo you want to get a free API token? (y/n): ").lower().strip()
    
    env_content = "# AI Research Paper Feed Configuration\nLLM_PROVIDER=huggingface\n\n"
    
    if use_token == 'y':
        print("\n📝 Getting your free Hugging Face token:")
        print("1. Go to: https://huggingface.co/settings/tokens")
        print("2. Click 'New token'")
        print("3. Give it a name like 'paper-feed'")
        print("4. Select 'Read' permissions")
        print("5. Copy the token")
        
        open_browser = input("\nOpen the website now? (y/n): ").lower().strip()
        if open_browser == 'y':
            webbrowser.open("https://huggingface.co/settings/tokens")
        
        token = input("\nPaste your token here (or press Enter to skip): ").strip()
        if token:
            env_content += f"HUGGINGFACE_API_KEY={token}\n"
        else:
            env_content += "# HUGGINGFACE_API_KEY=your_token_here\n"
    else:
        env_content += "# HUGGINGFACE_API_KEY=your_token_here\n"
    
    write_env_file(env_content)
    print("\n✅ Hugging Face setup complete!")

def setup_gemini():
    """Setup Google Gemini provider."""
    print("\n🧠 Setting up Google Gemini...")
    print("Gemini offers excellent quality with a generous free tier!")
    
    print("\n📝 Getting your free Gemini API key:")
    print("1. Go to: https://aistudio.google.com/")
    print("2. Sign in with your Google account")
    print("3. Click 'Get API key'")
    print("4. Create a new API key")
    print("5. Copy the key")
    
    open_browser = input("\nOpen the website now? (y/n): ").lower().strip()
    if open_browser == 'y':
        webbrowser.open("https://aistudio.google.com/")
    
    api_key = input("\nPaste your API key here: ").strip()
    
    env_content = f"""# AI Research Paper Feed Configuration
LLM_PROVIDER=gemini

# Google Gemini API Key (free tier)
GEMINI_API_KEY={api_key}
"""
    
    write_env_file(env_content)
    print("\n✅ Google Gemini setup complete!")

def setup_openai():
    """Setup OpenAI provider."""
    print("\n💰 Setting up OpenAI...")
    print("OpenAI provides the best quality but requires payment.")
    print("Cost is very low for testing (~$0.01-0.02 per session)")
    
    print("\n📝 Getting your OpenAI API key:")
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Sign in or create an account")
    print("3. Add billing information")
    print("4. Create a new API key")
    print("5. Copy the key")
    
    open_browser = input("\nOpen the website now? (y/n): ").lower().strip()
    if open_browser == 'y':
        webbrowser.open("https://platform.openai.com/api-keys")
    
    api_key = input("\nPaste your API key here: ").strip()
    
    env_content = f"""# AI Research Paper Feed Configuration
LLM_PROVIDER=openai

# OpenAI API Key (paid)
OPENAI_API_KEY={api_key}
"""
    
    write_env_file(env_content)
    print("\n✅ OpenAI setup complete!")

def write_env_file(content):
    """Write the .env file."""
    with open('.env', 'w') as f:
        f.write(content)
    print(f"\n📁 Created .env file in {os.getcwd()}")

def main():
    """Main setup function."""
    if os.path.exists('.env'):
        overwrite = input("⚠️ .env file already exists. Overwrite? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    create_env_file()
    
    print("\n🎉 Setup complete!")
    print("You can now run the app with: python main.py")
    print("\nTo test just the scraper: python test_app.py")

if __name__ == "__main__":
    main()
