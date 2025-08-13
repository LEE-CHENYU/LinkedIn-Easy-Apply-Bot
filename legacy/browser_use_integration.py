#!/usr/bin/env python3
"""
Integration module for browser-use with LinkedIn Easy Apply Bot
Provides enhanced form handling using AI automation
"""

import asyncio
import os
import time
import logging
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playwright.async_api import async_playwright
from browser_use_handler import LinkedInFormHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserUseLinkedInBot:
    """Enhanced LinkedIn bot with browser-use integration"""
    
    def __init__(self, config: Dict[str, Any], openai_api_key: str):
        """
        Initialize the enhanced LinkedIn bot
        
        Args:
            config: Configuration dictionary from config.yaml
            openai_api_key: OpenAI API key for browser-use
        """
        self.config = config
        self.api_key = openai_api_key
        self.form_handler = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.selenium_driver = None
        
    async def initialize_browser_use(self):
        """Initialize browser-use with playwright"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with similar settings to selenium
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Keep visible for debugging
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create new page
            self.page = await self.browser.new_page()
            
            # Initialize form handler
            self.form_handler = LinkedInFormHandler(self.config, self.api_key)
            await self.form_handler.initialize_agent(self.page)
            
            logger.info("Browser-use initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser-use: {str(e)}")
            raise
    
    async def sync_with_selenium(self, selenium_driver):
        """
        Sync browser-use with existing selenium session
        
        Args:
            selenium_driver: Existing selenium webdriver instance
        """
        try:
            self.selenium_driver = selenium_driver
            
            # Get current URL and cookies from selenium
            current_url = selenium_driver.current_url
            cookies = selenium_driver.get_cookies()
            
            # Navigate playwright to the same URL
            await self.page.goto(current_url)
            
            # Transfer cookies from selenium to playwright
            playwright_cookies = []
            for cookie in cookies:
                playwright_cookie = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie.get('path', '/'),
                }
                if 'expiry' in cookie:
                    playwright_cookie['expires'] = cookie['expiry']
                if 'httpOnly' in cookie:
                    playwright_cookie['httpOnly'] = cookie['httpOnly']
                if 'secure' in cookie:
                    playwright_cookie['secure'] = cookie['secure']
                    
                playwright_cookies.append(playwright_cookie)
            
            await self.page.context.add_cookies(playwright_cookies)
            
            # Refresh to ensure cookies are applied
            await self.page.reload()
            
            logger.info("Successfully synced browser-use with selenium session")
            
        except Exception as e:
            logger.error(f"Failed to sync with selenium: {str(e)}")
            raise
    
    async def handle_application_popup(self, job_title: str = "", company: str = "") -> bool:
        """
        Use browser-use to handle the entire application popup
        
        Args:
            job_title: Job title for context
            company: Company name for context
            
        Returns:
            bool: True if application was completed successfully
        """
        try:
            if not self.form_handler:
                raise Exception("Form handler not initialized")
            
            logger.info(f"Using AI to handle application for {job_title} at {company}")
            
            # Let the AI agent handle the entire form process
            success = await self.form_handler.handle_application_form(
                self.page, job_title, company
            )
            
            if success:
                logger.info("Application completed successfully using AI")
            else:
                logger.warning("AI application handling may have encountered issues")
                
            return success
            
        except Exception as e:
            logger.error(f"Error in AI application handling: {str(e)}")
            return False
    
    async def handle_specific_form_step(self, question_context: str) -> bool:
        """
        Handle a specific form step or question using AI
        
        Args:
            question_context: Context about the current form step
            
        Returns:
            bool: True if handled successfully
        """
        try:
            if not self.form_handler:
                raise Exception("Form handler not initialized")
                
            return await self.form_handler.handle_specific_question(
                self.page, question_context
            )
            
        except Exception as e:
            logger.error(f"Error handling specific form step: {str(e)}")
            return False
    
    async def close(self):
        """Clean up resources"""
        try:
            if self.form_handler:
                await self.form_handler.close()
            
            if self.page:
                await self.page.close()
                
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("Browser-use resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Integration helper functions for existing codebase
class LinkedInBotEnhancer:
    """Helper class to enhance existing LinkedIn bot with browser-use"""
    
    @staticmethod
    async def enhance_apply_to_job(
        linkedin_bot_instance, 
        openai_api_key: str,
        job_title: str = "Unknown", 
        company: str = "Unknown"
    ) -> bool:
        """
        Enhance the apply_to_job method with browser-use
        
        Args:
            linkedin_bot_instance: Instance of LinkedinEasyApply class
            openai_api_key: OpenAI API key
            job_title: Job title
            company: Company name
            
        Returns:
            bool: True if application was successful
        """
        browser_use_bot = None
        try:
            # Initialize browser-use bot
            browser_use_bot = BrowserUseLinkedInBot(
                linkedin_bot_instance.__dict__, 
                openai_api_key
            )
            
            await browser_use_bot.initialize_browser_use()
            
            # Sync with existing selenium session
            await browser_use_bot.sync_with_selenium(linkedin_bot_instance.browser)
            
            # Use AI to handle the application form
            success = await browser_use_bot.handle_application_popup(job_title, company)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in enhanced apply_to_job: {str(e)}")
            return False
            
        finally:
            if browser_use_bot:
                await browser_use_bot.close()


# Example integration with existing LinkedinEasyApply class
def create_enhanced_apply_method(openai_api_key: str):
    """
    Create an enhanced apply_to_job method that uses browser-use
    
    Args:
        openai_api_key: OpenAI API key
        
    Returns:
        Callable: Enhanced apply method
    """
    
    async def enhanced_apply_to_job(self, job_title="Unknown", company="Unknown"):
        """Enhanced apply_to_job method with AI form handling"""
        
        # First try the AI-powered approach
        try:
            success = await LinkedInBotEnhancer.enhance_apply_to_job(
                self, openai_api_key, job_title, company
            )
            
            if success:
                logger.info("Application completed successfully using AI")
                return True
            else:
                logger.warning("AI application failed, falling back to manual method")
                
        except Exception as e:
            logger.error(f"AI application error: {str(e)}, falling back to manual method")
        
        # Fallback to original method if AI fails
        try:
            # Call the original apply_to_job method
            return self.original_apply_to_job(job_title, company)
        except Exception as e:
            logger.error(f"Manual application also failed: {str(e)}")
            return False
    
    return enhanced_apply_to_job


# Configuration helper
def load_openai_api_key() -> str:
    """
    Load OpenAI API key from environment or .env file
    
    Returns:
        str: API key
    """
    # Try environment variable first
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        # Try loading from .env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"')
                        break
        except FileNotFoundError:
            pass
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set OPENAI_API_KEY environment variable "
            "or add it to .env file as OPENAI_API_KEY=your_key_here"
        )
    
    return api_key


# Example usage
async def test_integration():
    """Test the browser-use integration"""
    
    try:
        api_key = load_openai_api_key()
        print("✅ OpenAI API key loaded successfully")
        
        # Example config
        config = {
            'personalInfo': {
                'First Name': 'John',
                'Last Name': 'Doe',
            },
            'checkboxes': {
                'legallyAuthorized': True,
                'requireVisa': False,
            }
        }
        
        bot = BrowserUseLinkedInBot(config, api_key)
        await bot.initialize_browser_use()
        print("✅ Browser-use bot initialized successfully")
        
        await bot.close()
        print("✅ Integration test completed successfully")
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_integration())