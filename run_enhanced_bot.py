#!/usr/bin/env python3
"""
Main script to run the Enhanced LinkedIn Easy Apply Bot with AI-powered form handling
"""

import yaml
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from enhanced_linkedineasyapply import EnhancedLinkedInEasyApply


def setup_chrome_driver():
    """Setup Chrome WebDriver with optimized settings"""
    chrome_options = Options()
    
    # Add Chrome options for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # HIGH RESOLUTION AND ZOOM SETTINGS
    chrome_options.add_argument("--window-size=1920,1080")  # Set large window size
    chrome_options.add_argument("--start-maximized")        # Start maximized
    chrome_options.add_argument("--force-device-scale-factor=0.8")  # Zoom out to 80%
    chrome_options.add_argument("--high-dpi-support=1")     # Better DPI support
    chrome_options.add_argument("--device-scale-factor=0.8") # Additional zoom out
    
    # Uncomment the next line if you want to run in headless mode
    # chrome_options.add_argument("--headless")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set high resolution window
        driver.set_window_size(1920, 1080)
        driver.maximize_window()
        
        # Additional zoom out via JavaScript
        driver.execute_script("document.body.style.zoom='0.8'")
        
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver initialized with high resolution (1920x1080) and 80% zoom")
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {str(e)}")
        print("Please make sure ChromeDriver is installed and in PATH")
        return None


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print("❌ config.yaml not found! Please make sure it exists in the current directory.")
        return None
    except Exception as e:
        print(f"❌ Error loading config.yaml: {str(e)}")
        return None


async def main():
    """Main function to run the enhanced LinkedIn bot"""
    
    print("🚀 Starting Enhanced LinkedIn Easy Apply Bot with AI")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    print("✅ Configuration loaded successfully")
    
    # Setup WebDriver
    driver = setup_chrome_driver()
    if not driver:
        return
    
    print("✅ Chrome WebDriver initialized successfully")
    
    try:
        # Create enhanced bot instance
        bot = EnhancedLinkedInEasyApply(config, driver)
        print("✅ Enhanced LinkedIn bot created successfully")
        print(f"🤖 AI form handling: {'Enabled' if bot.use_ai_forms else 'Disabled'}")
        
        # Login to LinkedIn
        print("\n📝 Logging into LinkedIn...")
        bot.login()
        print("✅ Login completed")
        
        # Security check
        bot.security_check()
        
        # Start applying to jobs
        print("\n🎯 Starting job application process...")
        print("💡 The bot will use AI to handle complex application forms automatically!")
        print("💡 Manual form handling will be used as fallback if AI encounters issues.")
        
        bot.start_applying()
        
        # Print AI statistics
        bot.print_ai_stats()
        
    except KeyboardInterrupt:
        print("\n⏹️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            # Clean up AI resources
            if hasattr(bot, 'cleanup'):
                await bot.cleanup()
            
            # Close browser
            if driver:
                driver.quit()
                print("✅ Browser closed successfully")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")