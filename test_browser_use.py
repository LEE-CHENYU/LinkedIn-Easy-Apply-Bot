#!/usr/bin/env python3
"""
Test script for browser-use integration with LinkedIn Easy Apply Bot
"""

import asyncio
import os
import sys
import yaml
import logging
from browser_use_integration import BrowserUseLinkedInBot, load_openai_api_key

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_browser_use_basic():
    """Test basic browser-use functionality"""
    print("🧪 Testing basic browser-use functionality...")
    
    try:
        # Load API key
        api_key = load_openai_api_key()
        print("✅ OpenAI API key loaded successfully")
        
        # Create minimal config
        config = {
            'personalInfo': {
                'First Name': 'Test',
                'Last Name': 'User',
                'Mobile Phone Number': '555-0123',
                'Street address': '123 Test St',
                'City': 'Test City, NY',
                'State': 'New York',
                'Zip': '10001',
                'Linkedin': 'linkedin.com/in/testuser',
                'Website': 'github.com/testuser'
            },
            'checkboxes': {
                'legallyAuthorized': True,
                'requireVisa': False,
                'driversLicence': True,
                'urgentFill': True,
                'commute': True,
                'backgroundCheck': True
            },
            'technology': {
                'python': 5,
                'javascript': 3,
                'react': 2,
                'default': 1
            },
            'industry': {
                'Engineering': 3,
                'Information Technology': 4,
                'Product Management': 2,
                'default': 1
            },
            'universityGpa': '3.7',
            'languages': {
                'english': 'Native',
                'spanish': 'Conversational'
            }
        }
        
        # Initialize browser-use bot
        bot = BrowserUseLinkedInBot(config, api_key)
        await bot.initialize_browser_use()
        print("✅ Browser-use bot initialized successfully")
        
        # Test navigation to LinkedIn
        await bot.page.goto("https://www.linkedin.com/login")
        print("✅ Successfully navigated to LinkedIn login page")
        
        # Test form instructions generation
        instructions = bot.form_handler._build_form_instructions()
        print("✅ Form instructions generated successfully")
        print(f"📄 Instructions preview (first 200 chars): {instructions[:200]}...")
        
        # Clean up
        await bot.close()
        print("✅ Browser-use test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Browser-use test failed: {str(e)}")
        return False


async def test_linkedin_form_simulation():
    """Test handling of a simulated LinkedIn form"""
    print("\n🧪 Testing LinkedIn form simulation...")
    
    try:
        # Load API key
        api_key = load_openai_api_key()
        
        # Load actual config if available
        config_file = 'config.yaml'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print("✅ Loaded actual config.yaml")
        else:
            print("⚠️ config.yaml not found, using test config")
            return False
        
        # Initialize browser-use bot
        bot = BrowserUseLinkedInBot(config, api_key)
        await bot.initialize_browser_use()
        
        # Create a simple HTML form to simulate LinkedIn application form
        test_form_html = """
        <html>
        <head><title>Test LinkedIn Form</title></head>
        <body>
            <h2>Job Application Form</h2>
            <form>
                <div>
                    <label for="firstName">First Name:</label>
                    <input type="text" id="firstName" name="firstName" required>
                </div>
                <div>
                    <label for="lastName">Last Name:</label>
                    <input type="text" id="lastName" name="lastName" required>
                </div>
                <div>
                    <label for="phone">Phone Number:</label>
                    <input type="tel" id="phone" name="phone" required>
                </div>
                <div>
                    <label>Are you legally authorized to work in the US?</label>
                    <input type="radio" id="workAuthYes" name="workAuth" value="yes">
                    <label for="workAuthYes">Yes</label>
                    <input type="radio" id="workAuthNo" name="workAuth" value="no">
                    <label for="workAuthNo">No</label>
                </div>
                <div>
                    <label for="experience">Years of Python experience:</label>
                    <input type="number" id="experience" name="experience" min="0" max="20">
                </div>
                <button type="submit">Submit Application</button>
            </form>
        </body>
        </html>
        """
        
        # Load the test form
        await bot.page.set_content(test_form_html)
        print("✅ Test form loaded")
        
        # Test AI form handling
        success = await bot.handle_specific_form_step(
            "Please fill out this job application form with my information"
        )
        
        if success:
            print("✅ AI successfully handled the test form")
        else:
            print("⚠️ AI had issues with the test form")
        
        # Take a screenshot for verification
        await bot.page.screenshot(path="test_form_result.png")
        print("📸 Screenshot saved as test_form_result.png")
        
        # Clean up
        await bot.close()
        
        return success
        
    except Exception as e:
        print(f"❌ LinkedIn form simulation test failed: {str(e)}")
        return False


def test_environment_setup():
    """Test if the environment is properly set up for browser-use"""
    print("🧪 Testing environment setup...")
    
    try:
        # Test API key
        api_key = load_openai_api_key()
        print("✅ OpenAI API key found")
        
        # Test browser-use import
        from browser_use import Agent
        print("✅ browser-use library imported successfully")
        
        # Test playwright
        import playwright
        print("✅ Playwright imported successfully")
        
        # Test config file
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            print("✅ config.yaml loaded successfully")
            
            # Check required config sections
            required_sections = ['personalInfo', 'checkboxes', 'technology', 'industry']
            for section in required_sections:
                if section in config:
                    print(f"✅ {section} section found in config")
                else:
                    print(f"⚠️ {section} section missing from config")
        else:
            print("⚠️ config.yaml not found")
        
        print("✅ Environment setup test completed")
        return True
        
    except Exception as e:
        print(f"❌ Environment setup test failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting browser-use integration tests...\n")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Basic Browser-Use", test_browser_use_basic),
        ("LinkedIn Form Simulation", test_linkedin_form_simulation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Browser-use integration is ready.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")


if __name__ == "__main__":
    # Set up the browser-use environment
    os.environ['BROWSER_USE_ENV'] = 'browser-use'
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")