#!/usr/bin/env python3
"""
Quick test script for AI-only form handling
Use this to test if the AI integration is working properly
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your enhanced bot
from enhanced_linkedineasyapply import EnhancedLinkedInEasyApply
from linkedineasyapply import LinkedinEasyApply
import yaml
import time

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_ai_initialization():
    """Test if AI can be initialized properly"""
    print("🧪 Testing AI initialization...")
    
    config = load_config()
    if not config:
        print("❌ Could not load config.yaml")
        return False
    
    # Override to AI-only mode for testing
    config['formHandlingMode'] = 'ai-only'
    config['useAIForms'] = True
    config['debugMode'] = True
    
    try:
        # Create a dummy driver (we won't actually use it for this test)
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run headless for this test
        driver = webdriver.Chrome(options=options)
        
        # Initialize enhanced bot
        bot = EnhancedLinkedInEasyApply(config, driver)
        
        print(f"✅ Enhanced bot created")
        print(f"   - Form handling mode: {bot.form_handling_mode}")
        print(f"   - AI forms enabled: {bot.use_ai_forms}")
        print(f"   - OpenAI API key present: {'Yes' if bot.openai_api_key else 'No'}")
        
        # Test AI agent initialization
        import asyncio
        
        async def test_ai_agent():
            try:
                success = await bot.initialize_ai_agent()
                return success
            except Exception as e:
                print(f"❌ AI agent initialization error: {e}")
                return False
        
        # Run the test
        result = asyncio.run(test_ai_agent())
        
        if result:
            print("✅ AI agent initialized successfully!")
        else:
            print("❌ AI agent initialization failed")
        
        driver.quit()
        return result
        
    except Exception as e:
        print(f"❌ Error during AI test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI Integration Test")
    print("=" * 50)
    
    success = test_ai_initialization()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 AI integration test PASSED!")
        print("✅ Your AI should work properly now")
        print("\n💡 To use AI-only mode, add this to your config.yaml:")
        print("   formHandlingMode: 'ai-only'")
    else:
        print("❌ AI integration test FAILED")
        print("🔧 Check your .env file and OpenAI API key")
        print("\n💡 To use hardcoded-only mode, add this to your config.yaml:")
        print("   formHandlingMode: 'hardcoded-only'")