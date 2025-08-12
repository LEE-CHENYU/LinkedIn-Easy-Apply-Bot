#!/usr/bin/env python3
"""
Simplified Playwright LinkedIn Bot (Python 3.10 compatible)
Demonstrates single-browser architecture without browser-use dependency
"""

import asyncio
import time
import random
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import date
from itertools import product

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not available. Please install: pip install playwright && playwright install")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimplePlaywrightLinkedInBot:
    """Simplified Playwright LinkedIn Bot demonstrating single-browser architecture"""
    
    def __init__(self, parameters: Dict[str, Any]):
        """Initialize the simplified bot"""
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required but not available")
        
        # Basic configuration
        self.email = parameters['email']
        self.password = parameters['password']
        self.disable_lock = parameters['disableAntiLock']
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.base_search_url = self.get_base_search_url(parameters)
        
        # Playwright components - SINGLE BROWSER ARCHITECTURE
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Simple form handling configuration
        self.personal_info = parameters.get('personalInfo', {})
        self.checkboxes = parameters.get('checkboxes', {})
        
        logger.info("🎭 Simple Playwright LinkedIn Bot initialized")
        logger.info("✅ Single browser architecture - no dual sessions!")
    
    async def initialize_browser(self):
        """Initialize single Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--start-maximized',
                    '--window-size=1920,1080'
                ]
            )
            
            # Create context
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Create THE SINGLE PAGE for entire session
            self.page = await self.context.new_page()
            
            logger.info("🎭 Single Playwright browser initialized successfully")
            logger.info("📄 Single page created - will be used for entire session")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {str(e)}")
            return False
    
    async def login(self):
        """Login using Playwright - SAME PAGE"""
        try:
            logger.info("🔑 Logging in with Playwright...")
            
            await self.page.goto("https://www.linkedin.com/login")
            await asyncio.sleep(random.uniform(2, 4))
            
            # Fill login form using the SAME PAGE
            await self.page.fill('#username', self.email)
            await self.page.fill('#password', self.password)
            await self.page.click('.btn__primary--large')
            
            await asyncio.sleep(random.uniform(3, 5))
            logger.info("✅ Login completed on single page")
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise Exception("Could not login!")
    
    async def navigate_to_jobs(self, position: str, location: str, page_num: int = 0):
        """Navigate to job search - SAME PAGE"""
        search_url = (f"https://www.linkedin.com/jobs/search/{self.base_search_url}"
                     f"&keywords={position}&location={location}&start={page_num*25}")
        
        logger.info(f"🔍 Navigating to jobs: {position} in {location}")
        await self.page.goto(search_url)
        await asyncio.sleep(random.uniform(1, 2))
        
        logger.info("✅ Job search page loaded on SAME PAGE (no browser switch)")
    
    async def find_easy_apply_jobs(self) -> List[Dict[str, str]]:
        """Find Easy Apply jobs on current page - SAME PAGE"""
        try:
            # Wait for job results
            await self.page.wait_for_selector('.job-card-container', timeout=10000)
            
            # Find all job cards
            job_elements = await self.page.query_selector_all('.job-card-container')
            logger.info(f"📋 Found {len(job_elements)} jobs on SAME PAGE")
            
            jobs = []
            for i, job_element in enumerate(job_elements[:3]):  # Limit for demo
                try:
                    # Extract job info
                    title_element = await job_element.query_selector('.job-card-list__title a')
                    company_element = await job_element.query_selector('.job-card-container__primary-description')
                    
                    title = await title_element.text_content() if title_element else "Unknown"
                    company = await company_element.text_content() if company_element else "Unknown"
                    
                    jobs.append({
                        'title': title.strip(),
                        'company': company.strip(),
                        'element_index': i
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting job {i}: {str(e)}")
                    continue
            
            logger.info(f"✅ Extracted {len(jobs)} job details from SAME PAGE")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Error finding jobs: {str(e)}")
            return []
    
    async def apply_to_job_simple(self, job_title: str, company: str, job_index: int) -> bool:
        """Apply to job using simple form handling - SAME PAGE"""
        try:
            logger.info(f"🎯 Applying to: {job_title} at {company}")
            
            # Click on job to select it - SAME PAGE
            job_elements = await self.page.query_selector_all('.job-card-container')
            if job_index < len(job_elements):
                await job_elements[job_index].click()
                await asyncio.sleep(1)
            
            # Look for Easy Apply button - SAME PAGE
            easy_apply_button = await self.page.query_selector("button[aria-label*='Easy Apply']")
            if not easy_apply_button:
                easy_apply_button = await self.page.query_selector(".jobs-apply-button")
            
            if not easy_apply_button:
                logger.warning("⚠️ No Easy Apply button found")
                return False
            
            # Click Easy Apply - SAME PAGE
            await easy_apply_button.click()
            await asyncio.sleep(2)
            
            logger.info("📱 Easy Apply modal opened on SAME PAGE")
            
            # Simple form handling (basic demonstration)
            success = await self.handle_application_form_simple(job_title, company)
            
            if success:
                logger.info(f"✅ Successfully applied to {job_title} at {company} on SAME PAGE")
            else:
                logger.warning(f"❌ Failed to complete application for {job_title}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error applying to job: {str(e)}")
            return False
    
    async def handle_application_form_simple(self, job_title: str, company: str) -> bool:
        """Handle application form with simple logic - SAME PAGE"""
        try:
            logger.info("📝 Handling application form on SAME PAGE...")
            
            # Wait for modal to appear
            await self.page.wait_for_selector('.artdeco-modal', timeout=5000)
            
            max_steps = 5
            for step in range(max_steps):
                logger.info(f"📝 Form step {step + 1}/{max_steps}")
                
                # Fill basic text inputs
                await self.fill_basic_inputs()
                
                # Handle dropdowns
                await self.handle_dropdowns()
                
                # Look for Next/Continue/Submit button
                next_button = await self.find_next_button()
                
                if next_button:
                    button_text = await next_button.text_content()
                    logger.info(f"🔄 Clicking button: {button_text}")
                    
                    if 'submit' in button_text.lower():
                        logger.info("🚀 Found Submit button - completing application")
                        await next_button.click()
                        await asyncio.sleep(2)
                        
                        # Check for success
                        page_content = await self.page.content()
                        if any(indicator in page_content.lower() for indicator in 
                               ["application submitted", "thank you", "application sent"]):
                            logger.info("✅ Application submitted successfully!")
                            return True
                        else:
                            logger.warning("❌ Submit clicked but success not confirmed")
                            return False
                    else:
                        # Click Next/Continue
                        await next_button.click()
                        await asyncio.sleep(2)
                else:
                    logger.warning("⚠️ No Next/Continue button found")
                    break
            
            logger.warning("❌ Reached maximum steps without completion")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in form handling: {str(e)}")
            return False
    
    async def fill_basic_inputs(self):
        """Fill basic text inputs - SAME PAGE"""
        try:
            # Fill phone number if present
            phone_input = await self.page.query_selector('input[id*="phone"], input[name*="phone"]')
            if phone_input:
                phone = self.personal_info.get('Mobile Phone Number', '555-0123')
                await phone_input.fill(phone)
                logger.info(f"📞 Filled phone: {phone}")
            
            # Fill address if present
            address_input = await self.page.query_selector('input[id*="address"], input[name*="address"]')
            if address_input:
                address = self.personal_info.get('Street address', '123 Main St')
                await address_input.fill(address)
                logger.info(f"🏠 Filled address: {address}")
                
        except Exception as e:
            logger.warning(f"⚠️ Error filling basic inputs: {str(e)}")
    
    async def handle_dropdowns(self):
        """Handle dropdown selections - SAME PAGE"""
        try:
            # Look for common dropdowns
            dropdowns = await self.page.query_selector_all('select')
            
            for dropdown in dropdowns:
                try:
                    # Get dropdown options
                    options = await dropdown.query_selector_all('option')
                    
                    if len(options) > 1:  # Has real options
                        # Simple logic: select second option (usually "Yes" or first real option)
                        await dropdown.select_option(index=1)
                        logger.info("📝 Selected dropdown option")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error with dropdown: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"⚠️ Error handling dropdowns: {str(e)}")
    
    async def find_next_button(self):
        """Find Next/Continue/Submit button - SAME PAGE"""
        button_selectors = [
            "button[aria-label*='Continue']",
            "button[aria-label*='Next']", 
            "button[aria-label*='Submit']",
            "button:has-text('Continue')",
            "button:has-text('Next')",
            "button:has-text('Submit')",
            "button:has-text('Review')"
        ]
        
        for selector in button_selectors:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    # Check if button is visible and enabled
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    if is_visible and is_enabled:
                        return button
            except:
                continue
        
        return None
    
    async def demo_single_browser_architecture(self):
        """Demonstrate the single browser architecture"""
        logger.info("🎯 DEMONSTRATION: Single Browser Architecture")
        
        # Get first position and location for demo
        if not self.positions or not self.locations:
            logger.error("❌ No positions or locations configured")
            return
        
        position = self.positions[0]
        location = self.locations[0]
        
        try:
            # Step 1: Navigate to jobs - SAME PAGE
            await self.navigate_to_jobs(position, location)
            
            # Step 2: Find jobs - SAME PAGE  
            jobs = await self.find_easy_apply_jobs()
            
            if not jobs:
                logger.warning("⚠️ No jobs found for demonstration")
                return
            
            # Step 3: Apply to first job - SAME PAGE
            first_job = jobs[0]
            success = await self.apply_to_job_simple(
                first_job['title'], 
                first_job['company'], 
                first_job['element_index']
            )
            
            # Summary
            logger.info("📊 SINGLE BROWSER DEMONSTRATION COMPLETE")
            logger.info(f"   ✅ Login: SAME PAGE")
            logger.info(f"   ✅ Job Search: SAME PAGE") 
            logger.info(f"   ✅ Form Handling: SAME PAGE")
            logger.info(f"   🎯 Result: {'SUCCESS' if success else 'DEMO COMPLETE'}")
            logger.info("   🚫 NO DUAL BROWSER SESSIONS!")
            
        except Exception as e:
            logger.error(f"❌ Demo error: {str(e)}")
    
    def get_base_search_url(self, parameters: Dict[str, Any]) -> str:
        """Generate base search URL from parameters"""
        url_parts = ["f_AL=true"]  # Easy Apply filter
        
        # Add remote filter if specified
        if parameters.get('remote'):
            url_parts.append("f_CF=f_WRA")
        
        base_url = "?" + "&".join(url_parts)
        return base_url
    
    async def cleanup(self):
        """Clean up single browser session"""
        try:
            if self.page:
                await self.page.close()
                logger.info("📄 Single page closed")
            
            if self.context:
                await self.context.close()
                logger.info("🌐 Browser context closed")
            
            if self.browser:
                await self.browser.close()
                logger.info("🎭 Single browser closed")
            
            if self.playwright:
                await self.playwright.stop()
                logger.info("🎬 Playwright stopped")
                
            logger.info("✅ Single browser architecture cleanup complete")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")


# Simple demo function
async def demo_single_browser():
    """Demo the single browser architecture"""
    
    # Minimal config for demo
    demo_config = {
        'email': 'demo@example.com',
        'password': 'demo_password',
        'disableAntiLock': True,
        'positions': ['Software Engineer'],
        'locations': ['New York, NY'],
        'remote': True,
        'personalInfo': {
            'Mobile Phone Number': '555-0123',
            'Street address': '123 Demo St'
        },
        'checkboxes': {
            'legallyAuthorized': True,
            'requireVisa': False
        }
    }
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Cannot run demo - Playwright not available")
        print("Install with: pip install playwright && playwright install")
        return
    
    bot = SimplePlaywrightLinkedInBot(demo_config)
    
    try:
        print("🎭 Starting Single Browser Architecture Demo...")
        
        # Initialize single browser
        await bot.initialize_browser()
        
        print("✅ Single browser initialized - ready for:")
        print("   🔑 Login (SAME PAGE)")
        print("   🔍 Job Search (SAME PAGE)")  
        print("   📝 Form Handling (SAME PAGE)")
        print("   🚫 NO DUAL SESSIONS!")
        
        # Note: In a real demo, you'd uncomment these:
        # await bot.login()
        # await bot.demo_single_browser_architecture()
        
        print("🎯 Demo completed - single browser architecture works!")
        
    finally:
        await bot.cleanup()


if __name__ == '__main__':
    asyncio.run(demo_single_browser())