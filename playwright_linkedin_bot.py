#!/usr/bin/env python3
"""
Playwright-based LinkedIn Easy Apply Bot
Complete migration from Selenium to Playwright for single-browser AI-first architecture
"""

import asyncio
import time
import random
import csv
import traceback
import sys
import re
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import date
from itertools import product
from functools import wraps

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Try to import browser-use (requires Python 3.11+)
try:
    from browser_use import Agent, BrowserSession
    from browser_use.llm import ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ browser-use not available (requires Python 3.11+). AI features will be limited.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightLinkedInBot:
    """Pure Playwright LinkedIn Easy Apply Bot with integrated AI form handling"""
    
    def __init__(self, parameters: Dict[str, Any]):
        """Initialize the Playwright LinkedIn bot"""
        
        # Basic configuration
        self.email = parameters['email']
        self.password = parameters['password']
        self.disable_lock = parameters['disableAntiLock']
        self.blacklist_description_regex = parameters.get('blacklistDescriptionRegex', []) or []
        self.company_blacklist = parameters.get('companyBlacklist', []) or []
        self.title_blacklist = parameters.get('titleBlacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        self.file_name = "output"
        
        # Performance settings
        self.sleep_multiplier = 1.0
        self.fast_mode = parameters.get('fastMode', True)
        
        # Playwright components
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # AI configuration
        self.use_ai_forms = parameters.get('useAIForms', True)
        self.form_handling_mode = parameters.get('formHandlingMode', 'ai-only')
        self.ai_timeout = parameters.get('aiTimeout', 120)
        self.openai_api_key = self.load_openai_api_key()
        self.ai_success_count = 0
        self.ai_failure_count = 0
        
        # Form configuration for AI
        self.personal_info = parameters.get('personalInfo', {})
        self.checkboxes = parameters.get('checkboxes', {})
        self.technology = parameters.get('technology', {})
        self.industry = parameters.get('industry', {})
        self.university_gpa = parameters.get('universityGpa', '3.7')
        self.languages = parameters.get('languages', {})
        
        logger.info("🎭 Playwright LinkedIn Bot initialized")
        logger.info(f"🤖 AI form handling: {'Enabled' if self.use_ai_forms else 'Disabled'}")
        logger.info(f"🔧 Form handling mode: {self.form_handling_mode}")
        logger.info(f"⏱️ AI timeout: {self.ai_timeout} seconds")
    
    def load_openai_api_key(self) -> Optional[str]:
        """Load OpenAI API key from environment or .env file"""
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
        
        if api_key:
            logger.info("✅ OpenAI API key loaded successfully")
        else:
            logger.warning("⚠️ OpenAI API key not found - AI features will be disabled")
            
        return api_key
    
    async def initialize_browser(self):
        """Initialize Playwright browser with optimized settings"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with similar settings to Selenium but optimized
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Keep visible for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--start-maximized',
                    '--disable-extensions',
                    '--ignore-certificate-errors',
                    '--window-size=1920,1080'
                ]
            )
            
            # Create browser context with proper settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            
            # Create main page
            self.page = await self.context.new_page()
            
            logger.info("🎭 Playwright browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright browser: {str(e)}")
            return False
    
    
    async def login(self):
        """Login to LinkedIn using Playwright"""
        try:
            logger.info("🔑 Starting LinkedIn login...")
            
            await self.page.goto("https://www.linkedin.com/login")
            await asyncio.sleep(random.uniform(2, 4) * self.sleep_multiplier)
            
            # Fill login form
            await self.page.fill('#username', self.email)
            await self.page.fill('#password', self.password)
            await self.page.click('.btn__primary--large')
            
            await asyncio.sleep(random.uniform(3, 5) * self.sleep_multiplier)
            
            logger.info("✅ Login completed")
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise Exception("Could not login!")
    
    async def security_check(self):
        """Handle LinkedIn security check if present"""
        current_url = self.page.url
        page_content = await self.page.content()
        
        if '/checkpoint/challenge/' in current_url or 'security check' in page_content.lower():
            logger.warning("🔒 Security check detected")
            print("Please complete the security check and press enter in this console when it is done.")
            input()
            await asyncio.sleep(random.uniform(5.5, 10.5))
            logger.info("✅ Security check completed")
    
    async def start_applying(self):
        """Main job application loop"""
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        
        page_sleep = 0
        minimum_time = 15 * 1
        minimum_page_time = time.time() + minimum_time
        
        logger.info(f"🚀 Starting job applications for {len(searches)} search combinations")
        
        for (position, location) in searches:
            location_url = "&location=" + location
            job_page_number = -1
            
            logger.info(f"🔍 Starting search for {position} in {location}")
            
            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.info(f"📄 Going to job page {job_page_number}")
                    
                    await self.next_job_page(position, location_url, job_page_number)
                    await asyncio.sleep(random.uniform(1, 2) * self.sleep_multiplier)
                    
                    logger.info("🎯 Starting application process for this page...")
                    logger.info("🔒 PAGE LOCK: Will process ALL jobs on this page before navigating")
                    await self.apply_jobs(location)
                    logger.info("✅ Applying to jobs on this page completed!")
                    logger.info("🔓 PAGE UNLOCK: Ready to navigate to next page")
                    
                    # Sleep management
                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        logger.info(f"😴 Sleeping for {time_left:.1f} seconds")
                        await asyncio.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                        
                    if page_sleep % 5 == 0:
                        if self.fast_mode:
                            sleep_time = random.randint(60, 120)
                        else:
                            sleep_time = random.randint(120, 240)
                        logger.info(f"😴 Extended sleep for {sleep_time/60:.1f} minutes")
                        await asyncio.sleep(sleep_time)
                        page_sleep += 1
                        
            except Exception as e:
                logger.error(f"❌ Error in job search loop: {str(e)}")
                traceback.print_exc()
                continue
    
    async def next_job_page(self, position: str, location: str, job_page: int):
        """Navigate to next job search page"""
        search_url = (f"https://www.linkedin.com/jobs/search/{self.base_search_url}"
                     f"&keywords={position}{location}&start={job_page*25}")
        
        await self.page.goto(search_url)
        await self.avoid_lock()
    
    async def apply_jobs(self, location: str):
        """Apply to jobs on current page with progress tracking"""
        
        # Initialize page job tracking
        page_job_tracker = {
            'total_jobs': 0,
            'processed_jobs': 0,
            'applied_jobs': 0,
            'skipped_jobs': 0,
            'failed_jobs': 0,
            'current_job_index': 0,
            'job_statuses': {}  # Track status of each job by index
        }
        
        # Check for no jobs message
        try:
            no_jobs_element = await self.page.query_selector('.jobs-search-two-pane__no-results-banner--expand')
            if no_jobs_element:
                no_jobs_text = await no_jobs_element.text_content()
                if 'No matching jobs found' in no_jobs_text:
                    raise Exception("No more jobs on this page")
        except:
            pass
        
        page_content = await self.page.content()
        if 'unfortunately, things aren' in page_content.lower():
            raise Exception("No more jobs on this page")
        
        # Debug: Save page source
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(page_content)
        logger.info(f"📊 Current URL: {self.page.url}")
        
        # Check login status
        if 'sign in' in page_content.lower() or '/login' in self.page.url.lower():
            logger.warning("⚠️ May not be logged in properly")
            raise Exception("Login required or session expired")
        
        # Wait for job results to load
        try:
            await self.page.wait_for_selector('.job-card-container', timeout=10000)
            
            # Find all job elements
            job_elements = await self.page.query_selector_all('.job-card-container')
            page_job_tracker['total_jobs'] = len(job_elements)
            
            logger.info(f"📋 Found {len(job_elements)} job listings on page")
            logger.info(f"📊 Starting page job tracking - will process ALL {len(job_elements)} jobs before navigation")
            
            if not job_elements:
                logger.warning("⚠️ No job elements found")
                return
            
            # Scroll through jobs list
            job_results = await self.page.query_selector('.jobs-search-results-list')
            if job_results:
                await self.scroll_slow_playwright(job_results)
                await self.scroll_slow_playwright(job_results, step=300, reverse=True)
            
            # Process each job with tracking
            for index, job_element in enumerate(job_elements):
                try:
                    page_job_tracker['current_job_index'] = index
                    
                    # Log progress
                    logger.info(f"📈 Page Progress: {page_job_tracker['processed_jobs']}/{page_job_tracker['total_jobs']} jobs processed")
                    logger.info(f"   ✅ Applied: {page_job_tracker['applied_jobs']}, ⏭️ Skipped: {page_job_tracker['skipped_jobs']}, ❌ Failed: {page_job_tracker['failed_jobs']}")
                    
                    # Extract job information
                    job_title, company = await self.extract_job_info(job_element)
                    
                    if not job_title or not company:
                        logger.warning(f"⚠️ Skipping job {index+1} - missing title or company")
                        page_job_tracker['skipped_jobs'] += 1
                        page_job_tracker['job_statuses'][index] = 'skipped_no_info'
                        page_job_tracker['processed_jobs'] += 1
                        continue
                    
                    logger.info(f"🎯 Processing job {index+1}/{page_job_tracker['total_jobs']}: {job_title} at {company}")
                    
                    # Check blacklists
                    if self.is_blacklisted(job_title, company):
                        logger.info(f"⛔ Skipping blacklisted job: {job_title} at {company}")
                        page_job_tracker['skipped_jobs'] += 1
                        page_job_tracker['job_statuses'][index] = 'blacklisted'
                        page_job_tracker['processed_jobs'] += 1
                        continue
                    
                    # Click on job to view details
                    await job_element.click()
                    await asyncio.sleep(random.uniform(1, 2) * self.sleep_multiplier)
                    
                    # Try to apply with page context
                    success = await self.apply_to_job_with_context(job_title, company, page_job_tracker)
                    
                    if success:
                        logger.info(f"✅ Successfully applied to {job_title} at {company}")
                        page_job_tracker['applied_jobs'] += 1
                        page_job_tracker['job_statuses'][index] = 'applied'
                    else:
                        logger.info(f"❌ Failed to apply to {job_title} at {company}")
                        page_job_tracker['failed_jobs'] += 1
                        page_job_tracker['job_statuses'][index] = 'failed'
                        
                        # CRITICAL: Force close any open modals after failure
                        logger.info("🔄 Closing application modal after failure...")
                        await self.force_close_all_modals()
                        
                        # Ensure we're back on job listings
                        await asyncio.sleep(1)
                        current_url = self.page.url
                        if '/jobs/view/' in current_url:
                            logger.info("📍 Still on job view, returning to listings...")
                            await self.page.keyboard.press("Escape")
                            await asyncio.sleep(0.5)
                    
                    page_job_tracker['processed_jobs'] += 1
                    
                    # Small delay between applications
                    await asyncio.sleep(random.uniform(2, 4) * self.sleep_multiplier)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing job {index+1}: {str(e)}")
                    page_job_tracker['failed_jobs'] += 1
                    page_job_tracker['job_statuses'][index] = 'error'
                    page_job_tracker['processed_jobs'] += 1
                    continue
            
            # Final page summary
            logger.info(f"✅ PAGE COMPLETE - Processed all {page_job_tracker['total_jobs']} jobs")
            logger.info(f"📊 Final Stats: Applied: {page_job_tracker['applied_jobs']}, Skipped: {page_job_tracker['skipped_jobs']}, Failed: {page_job_tracker['failed_jobs']}")
        
        except Exception as e:
            logger.error(f"❌ Error in apply_jobs: {str(e)}")
            raise
    
    async def extract_job_info(self, job_element) -> tuple[str, str]:
        """Extract job title and company from job element"""
        try:
            # Try multiple selectors for job title
            title_selectors = [
                '.job-card-list__title a',
                '.job-card-list__title',
                'a[data-control-name="job_card_title_link"]',
                '[data-job-title]',
                'h3.job-card-list__title',
                'a.job-card-list__title',
                '.job-card-container__link span[aria-hidden="true"]'
            ]
            
            job_title = "Unknown"
            for selector in title_selectors:
                title_element = await job_element.query_selector(selector)
                if title_element:
                    text = await title_element.text_content()
                    if text and text.strip():
                        job_title = text.strip()
                        logger.debug(f"Found job title with selector {selector}: {job_title}")
                        break
            
            # Try multiple selectors for company
            company_selectors = [
                '.job-card-container__primary-description',
                '.job-card-container__company-name',
                'a[data-control-name="company_link"]',
                '[data-job-company]',
                'h4.job-card-container__company-name',
                'a.job-card-container__company-name',
                '.job-card-container__primary-description a'
            ]
            
            company = "Unknown"
            for selector in company_selectors:
                company_element = await job_element.query_selector(selector)
                if company_element:
                    text = await company_element.text_content()
                    if text and text.strip():
                        company = text.strip()
                        logger.debug(f"Found company with selector {selector}: {company}")
                        break
            
            # Log if we couldn't find info
            if job_title == "Unknown" or company == "Unknown":
                logger.warning(f"⚠️ Could not extract full job info - Title: {job_title}, Company: {company}")
            
            return job_title, company
            
        except Exception as e:
            logger.error(f"❌ Error extracting job info: {str(e)}")
            return "Unknown", "Unknown"
    
    async def apply_to_job_with_context(self, job_title: str, company: str, page_tracker: dict) -> bool:
        """Apply to job with page context for AI"""
        # Store page context for AI prompt
        self.current_page_tracker = page_tracker
        return await self.apply_to_job(job_title, company)
    
    async def apply_to_job(self, job_title: str = "Unknown", company: str = "Unknown") -> bool:
        """Apply to a specific job using AI-first approach"""
        
        # Look for Easy Apply button
        easy_apply_selectors = [
            '.jobs-apply-button',
            "button[aria-label*='Easy Apply']",
            "button.jobs-apply-button",
            "button[class*='jobs-apply']"
        ]
        
        easy_apply_button = None
        for selector in easy_apply_selectors:
            easy_apply_button = await self.page.query_selector(selector)
            if easy_apply_button:
                break
        
        if not easy_apply_button:
            logger.warning("⚠️ No Easy Apply button found")
            return False
        
        try:
            # Scroll job description area
            job_description_area = await self.page.query_selector('.jobs-search__job-details--container')
            if job_description_area:
                await self.scroll_slow_playwright(job_description_area, end=1600)
                await self.scroll_slow_playwright(job_description_area, end=1600, step=400, reverse=True)
        except:
            pass
        
        logger.info(f"📋 Applying to job: {job_title} at {company}")
        logger.info(f"🤖 AI form handling: {'Enabled' if self.use_ai_forms else 'Disabled'}")
        
        # Click Easy Apply button
        await easy_apply_button.click()
        await asyncio.sleep(2 * self.sleep_multiplier)
        
        logger.info("📱 Application modal opened")
        
        # Handle application based on mode
        if self.form_handling_mode == 'ai-only' and self.use_ai_forms and self.openai_api_key:
            logger.info("🤖 Using AI-only form handling...")
            return await self.apply_with_ai(job_title, company)
        else:
            logger.warning("❌ Non-AI modes not implemented in this version")
            return False
    
    async def force_close_all_modals(self):
        """Forcefully close ALL modals and windows - hardcoded aggressive approach"""
        logger.info("🔨 FORCE CLOSING ALL MODALS (hardcoded recovery)")
        
        try:
            # Step 0: Check if we're in an "Apply to [Company]" modal
            try:
                modal_header = await self.page.query_selector("h2.jobs-easy-apply-modal__title")
                if not modal_header:
                    modal_header = await self.page.query_selector("h2:has-text('Apply to')")
                
                if modal_header:
                    header_text = await modal_header.text_content()
                    logger.info(f"📋 Detected application modal: {header_text}")
                    
                    # Try to find the X/Dismiss button specifically for this modal
                    dismiss_button = await self.page.query_selector(".artdeco-modal__dismiss")
                    if dismiss_button and await dismiss_button.is_visible():
                        logger.info("✅ Found modal dismiss button, clicking...")
                        await dismiss_button.click(force=True)
                        await asyncio.sleep(1)
                        return  # Successfully closed
            except:
                pass
            
            # Step 1: Press Escape multiple times
            logger.info("⌨️ Pressing Escape 5 times...")
            for i in range(5):
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.3)
            
            # Step 2: Try ALL possible close button selectors
            close_selectors = [
                # LinkedIn Application Modal specific (PRIORITY)
                ".artdeco-modal__dismiss",  # The X button on LinkedIn modals
                ".artdeco-modal__dismiss-icon",
                "button[aria-label='Dismiss']",
                ".jobs-easy-apply-modal button[aria-label='Dismiss']",
                ".jobs-easy-apply-modal .artdeco-modal__dismiss",
                "[data-test-modal-close-btn]",
                "[data-control-name='discard_application']",
                
                # Standard close buttons
                "button:has-text('Close')",
                "button:has-text('Cancel')",
                "button:has-text('Done')",
                "button:has-text('Dismiss')",
                "button:has-text('X')",
                "button:has-text('x')",
                "button:has-text('✕')",
                "button:has-text('×')",
                
                # Aria labels
                "[aria-label='Close']",
                "[aria-label='Dismiss']",
                "[aria-label='Cancel']",
                "[aria-label*='close' i]",
                "[aria-label*='dismiss' i]",
                
                # Generic modal close
                ".modal-close",
                ".close-modal",
                ".btn-close",
                "[data-dismiss='modal']",
                
                # SVG/Icon close buttons
                "svg[aria-label='Close']",
                "svg[aria-label='Dismiss']",
                
                # Any button with role
                "[role='button'][aria-label*='Close' i]",
                "[role='button'][aria-label*='Dismiss' i]"
            ]
            
            logger.info(f"🔍 Searching for close buttons with {len(close_selectors)} selectors...")
            closed = False
            for selector in close_selectors:
                try:
                    buttons = await self.page.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            logger.info(f"✅ Found close button: {selector}")
                            await button.click(force=True)  # Force click even if intercepted
                            await asyncio.sleep(0.5)
                            closed = True
                            break
                except Exception as e:
                    continue
                if closed:
                    break
            
            # Step 3: Click outside any modals (multiple positions)
            logger.info("🖱️ Clicking outside modals at multiple positions...")
            click_positions = [
                {"x": 10, "y": 10},
                {"x": 100, "y": 100},
                {"x": 50, "y": 200},
                {"x": 300, "y": 50}
            ]
            for pos in click_positions:
                try:
                    await self.page.click("body", position=pos, force=True)
                    await asyncio.sleep(0.2)
                except:
                    pass
            
            # Step 4: Try to find ANY button with close-related text
            logger.info("🔍 Searching ALL buttons for close-related text...")
            try:
                all_buttons = await self.page.query_selector_all("button")
                logger.info(f"Found {len(all_buttons)} total buttons on page")
                
                close_words = ['close', 'cancel', 'dismiss', 'done', 'x', '×', '✕', 'discard', 'exit', 'back']
                for button in all_buttons[:20]:  # Check first 20 buttons
                    try:
                        text = await button.text_content()
                        if text and any(word in text.lower() for word in close_words):
                            logger.info(f"📍 Found button with text: {text}")
                            await button.click(force=True)
                            await asyncio.sleep(0.5)
                            break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"⚠️ Error checking all buttons: {str(e)}")
            
            # Step 5: Final escape attempts
            logger.info("⌨️ Final Escape key attempts...")
            for _ in range(3):
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.2)
            
            # Step 6: Check if we need to navigate away
            current_url = self.page.url
            if '/jobs/view/' in current_url or 'application' in current_url.lower():
                logger.info("🔄 Still on application page, navigating back to job search...")
                await self.page.goto("https://linkedin.com/jobs/search/", wait_until='domcontentloaded')
                await asyncio.sleep(2)
            
            logger.info("✅ Force close sequence completed")
            
        except Exception as e:
            logger.error(f"❌ Error in force_close_all_modals: {str(e)}")
            # Last resort - navigate away
            try:
                logger.info("🚨 LAST RESORT: Navigating to job search page...")
                await self.page.goto("https://linkedin.com/jobs/search/", wait_until='domcontentloaded')
            except:
                pass

    async def handle_application_success(self) -> bool:
        """Handle success modal after application submission"""
        try:
            logger.info("🔄 Handling application success modal...")
            
            # Try to close modal with various selectors
            dismiss_selectors = [
                "[aria-label='Dismiss']",
                "[aria-label*='Dismiss']",
                "button:has-text('Done')",
                "button:has-text('Close')",
                "[data-test-modal-close-btn]",
                ".artdeco-modal__dismiss",
                ".artdeco-modal__dismiss-icon",
                "button[aria-label*='Close']",
                "svg[aria-label='Dismiss']"
            ]
            
            for selector in dismiss_selectors:
                try:
                    # Look for the dismiss button
                    button = await self.page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        if is_visible:
                            logger.info(f"📍 Found dismiss button: {selector}")
                            await button.click()
                            logger.info("✅ Clicked dismiss button")
                            await asyncio.sleep(2)
                            return True
                except Exception as e:
                    logger.debug(f"Couldn't click {selector}: {str(e)}")
                    continue
            
            # If no button found, try pressing Escape
            logger.info("⌨️ No dismiss button found, pressing Escape")
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            # Also try clicking outside the modal
            try:
                await self.page.click("body", position={"x": 10, "y": 10})
                logger.info("🖱️ Clicked outside modal")
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling success modal: {str(e)}")
            return False
    
    async def apply_with_ai(self, job_title: str, company: str) -> bool:
        """Apply to job using AI form handling"""
        
        if not BROWSER_USE_AVAILABLE:
            logger.error("❌ browser-use not available. Please use Python 3.11+ and install browser-use")
            return False
            
        try:
            logger.info(f"🎯 AI applying to: {job_title} at {company}")
            
            # Build AI instructions
            instructions = self.build_ai_instructions(job_title, company)
            
            # Create LLM instance
            llm = ChatOpenAI(
                model="gpt-5-mini",
                api_key=self.openai_api_key
            )
            
            # Create new agent with specific task for this application
            agent = Agent(
                task=instructions,
                llm=llm,
                browser_session=BrowserSession(page=self.page),
                use_vision=True,
                save_conversation_path="./logs/browser_use_conversations"
            )
            
            # Run AI agent with timeout
            try:
                result = await asyncio.wait_for(
                    agent.run(max_steps=15),
                    timeout=self.ai_timeout
                )
                
                # Check if application was successful
                page_content = await self.page.content()
                success_indicators = [
                    "application submitted",
                    "your application has been submitted",
                    "application sent",
                    "thank you for applying",
                    "application received"
                ]
                
                if any(indicator in page_content.lower() for indicator in success_indicators):
                    self.ai_success_count += 1
                    logger.info("✅ AI successfully completed application")
                    
                    # Handle success modal
                    await self.handle_application_success()
                    
                    return True
                else:
                    self.ai_failure_count += 1
                    logger.warning("❌ AI application may not have been submitted")
                    
                    # Force close modal after unsuccessful application
                    logger.info("🔄 Closing modal after unsuccessful submission...")
                    await self.force_close_all_modals()
                    
                    return False
                    
            except asyncio.TimeoutError:
                self.ai_failure_count += 1
                logger.error(f"❌ AI application timed out after {self.ai_timeout} seconds")
                
                # HARDCODED FORCEFUL MODAL CLOSING
                logger.info("⚠️ Timeout occurred - starting forceful modal closing...")
                await self.force_close_all_modals()
                
                # Double-check we're back on job search
                current_url = self.page.url
                if '/jobs/view/' in current_url or 'application' in current_url.lower():
                    logger.info("🔄 Still stuck after force close, navigating to job search...")
                    try:
                        await self.page.goto("https://linkedin.com/jobs/search/", wait_until='domcontentloaded', timeout=10000)
                    except:
                        logger.error("❌ Failed to navigate back to job search")
                
                logger.info("✅ Recovered from timeout, ready for next job")
                return False
                
        except Exception as e:
            self.ai_failure_count += 1
            logger.error(f"❌ AI application error: {str(e)}")
            
            # Force close modal after any error
            logger.info("🔄 Closing modal after error...")
            try:
                await self.force_close_all_modals()
            except:
                pass
            
            return False
    
    def build_ai_instructions(self, job_title: str, company: str) -> str:
        """Build comprehensive AI instructions for form filling"""
        
        # Add page progress context if available
        page_context = ""
        if hasattr(self, 'current_page_tracker') and self.current_page_tracker:
            tracker = self.current_page_tracker
            page_context = f"""
📊 CURRENT PAGE PROGRESS:
- Processing job {tracker.get('current_job_index', 0) + 1} of {tracker.get('total_jobs', 0)} on this page
- Jobs processed so far: {tracker.get('processed_jobs', 0)}
- Applied: {tracker.get('applied_jobs', 0)}, Skipped: {tracker.get('skipped_jobs', 0)}, Failed: {tracker.get('failed_jobs', 0)}
- ⚠️ DO NOT NAVIGATE AWAY from this job listing page - we need to process all {tracker.get('total_jobs', 0)} jobs
- After completing or closing this application, return to the job listings to continue
"""
        
        instructions = f"""
You are helping fill out a LinkedIn job application for {job_title} at {company}. 
{page_context}
⚠️ MOST IMPORTANT: Always prioritize clicking Next, Continue, Review, and Submit buttons to progress through the form. Don't get stuck on one page - keep moving forward!

⚠️ CRITICAL: If you see "Apply to [Company Name]" modal window (like "Apply to TikTok"), this is an application form. 
   - If you can complete it: Fill the form and click Submit Application
   - If you CANNOT proceed: IMMEDIATELY click the X button (.artdeco-modal__dismiss) in the top-right corner
   - DO NOT leave the modal open - you MUST either submit or close it
   - If stuck for more than 30 seconds, close the modal immediately

⚠️ PAGE NAVIGATION: DO NOT navigate to a different page. Stay on the current job listings page and only work within the application modal/form.

PERSONAL INFORMATION:
- First Name: {self.personal_info.get('First Name', 'John')}
- Last Name: {self.personal_info.get('Last Name', 'Doe')}
- Phone: {self.personal_info.get('Mobile Phone Number', '555-0123')}
- Email: Use any existing email field values
- Address: {self.personal_info.get('Street address', '123 Main St')}
- City: {self.personal_info.get('City', 'New York, NY')}
- State: {self.personal_info.get('State', 'New York')}
- ZIP: {self.personal_info.get('Zip', '10001')}
- LinkedIn: {self.personal_info.get('Linkedin', 'linkedin.com/in/profile')}
- Website: {self.personal_info.get('Website', 'github.com/profile')}

WORK AUTHORIZATION:
- Legally authorized to work in US: {'Yes' if self.checkboxes.get('legallyAuthorized', True) else 'No'}
- Require visa sponsorship: {'Yes' if self.checkboxes.get('requireVisa', False) else 'No'}
- Have driver's license: {'Yes' if self.checkboxes.get('driversLicence', True) else 'No'}
- Can start immediately: {'Yes' if self.checkboxes.get('urgentFill', True) else 'No'}
- Comfortable commuting: {'Yes' if self.checkboxes.get('commute', True) else 'No'}
- Background check: {'Yes' if self.checkboxes.get('backgroundCheck', True) else 'No'}

EDUCATION:
- GPA: {self.university_gpa}
- Completed degrees: {', '.join(self.checkboxes.get('degreeCompleted', ["Bachelor's Degree"]))}

EXPERIENCE (in years):
Technology Skills: {dict(list(self.technology.items())[:5])}
Industry Experience: {dict(list(self.industry.items())[:5])}
Default experience for unlisted skills: {self.technology.get('default', 1)} years

LANGUAGES:
{self.languages}

IMPORTANT RULES:
1. For "years of experience" questions, match the technology/skill mentioned to the values above
2. For yes/no questions, use the work authorization values above
3. For dropdown selections, choose the most appropriate option based on the context
4. For text fields without specific matches, use reasonable defaults
5. For file uploads, skip them (they should be handled separately)
6. For EEO questions (gender, race, veteran status), select "Prefer not to answer" or "Decline to answer"

BUTTON PRIORITY (ALWAYS DO THIS):
7. PRIORITIZE clicking these buttons when visible:
   - "Next" button - click immediately when visible to move forward
   - "Review" or "Review Application" button - click to review before submission
   - "Submit" or "Submit Application" button - click when all fields are filled
   - "Continue" button - click to proceed through multi-step forms
8. After filling each section, ALWAYS look for and click Next/Continue/Review buttons
9. Don't stay on the same page - always progress forward by clicking navigation buttons
10. If you see "Submit Application", only click it if all required fields are properly filled

CRITICAL BUTTON DETECTION AND PRIORITY:
11. ALWAYS scroll down to check for navigation buttons at the bottom of the page
12. Many LinkedIn forms have buttons stuck at the bottom that are not visible without scrolling
13. PRIORITY ORDER for clicking buttons:
    a. First priority: "Next" button (to move to next section)
    b. Second priority: "Continue" button (to proceed)
    c. Third priority: "Review" or "Review Application" (before final submission)
    d. Fourth priority: "Submit" or "Submit Application" (final step)
14. After filling ANY form section, immediately look for and click Next/Continue
15. If you cannot find navigation buttons, scroll down completely and look again
16. Don't wait - click navigation buttons as soon as they're available

SCROLLING INSTRUCTIONS:
- Always scroll down to reveal hidden form elements and buttons
- Some forms have multiple sections that only become visible after scrolling
- Check both top and bottom of the page for navigation buttons
- If stuck, try scrolling to reveal more content or buttons

APPLICATION MODAL HANDLING ("Apply to [Company]" windows):
17. When you see a modal with "Apply to TikTok" or similar header:
    - This is the main application form window
    - Complete the form by filling fields and clicking Next/Submit
    - If you cannot proceed or get stuck:
      * Look for the X button in the top-right corner of the modal
      * The dismiss button is usually .artdeco-modal__dismiss
      * Click it to close the modal and move to next job
    - Don't leave modals open - either complete or close them

IMPORTANT - DO NOT CLICK OTHER JOBS:
18. DO NOT click on other job listings in the background
    - Focus ONLY on the current application modal
    - Do not navigate to other jobs on the page
    - The system will automatically move to the next job after this one
    - Stay within the current modal/form until completed or closed

STUCK STATE RECOVERY:
19. If completely stuck on any form or modal:
    - PRIORITY: Click the X button in top-right corner of modal (.artdeco-modal__dismiss)
    - Look for Close, Cancel, Dismiss, or X buttons
    - Press Escape key multiple times
    - Navigate away if nothing else works
    - Don't waste time - close stuck forms and continue

FAILURE HANDLING:
20. If you determine the application CANNOT be submitted:
    - IMMEDIATELY close the modal using the X button
    - Do not keep trying the same failing action
    - Report "Application could not be completed" and close the modal
    - The system needs the modal closed to move to the next job
    - Leaving the modal open will block all other jobs

Please fill out this LinkedIn job application form step by step, following these instructions carefully.
"""
        
        return instructions.strip()
    
    def is_blacklisted(self, job_title: str, company: str) -> bool:
        """Check if job/company is blacklisted"""
        
        # Check company blacklist
        for blacklisted_company in self.company_blacklist:
            if blacklisted_company.lower() in company.lower():
                return True
        
        # Check title blacklist
        for blacklisted_title in self.title_blacklist:
            if blacklisted_title.lower() in job_title.lower():
                return True
        
        return False
    
    async def scroll_slow_playwright(self, element, start: int = 0, end: int = 3600, 
                                   step: int = 100, reverse: bool = False):
        """Playwright version of slow scrolling"""
        try:
            if reverse:
                start, end = end, start
                step = -step
            
            for i in range(start, end, step):
                await element.evaluate(f'element => element.scrollTop = {i}')
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.warning(f"⚠️ Scroll error: {str(e)}")
    
    async def avoid_lock(self):
        """Anti-detection measures"""
        if not self.disable_lock:
            await asyncio.sleep(random.uniform(0.5, 1.0))
    
    def get_base_search_url(self, parameters: Dict[str, Any]) -> str:
        """Generate base search URL from parameters"""
        
        url_parts = []
        
        # Remote filter
        if parameters.get('remote'):
            url_parts.append("f_CF=f_WRA")
        
        # Experience level
        experience_level = parameters.get('experienceLevel', {})
        experience_filters = []
        if experience_level.get('internship'):
            experience_filters.append('1')
        if experience_level.get('entry'):
            experience_filters.append('2')
        if experience_level.get('associate'):
            experience_filters.append('3')
        if experience_level.get('mid-senior level'):
            experience_filters.append('4')
        if experience_level.get('director'):
            experience_filters.append('5')
        if experience_level.get('executive'):
            experience_filters.append('6')
        
        if experience_filters:
            url_parts.append(f"f_E={','.join(experience_filters)}")
        
        # Job types
        job_types = parameters.get('jobTypes', {})
        job_type_filters = []
        if job_types.get('full-time'):
            job_type_filters.append('F')
        if job_types.get('contract'):
            job_type_filters.append('C')
        if job_types.get('part-time'):
            job_type_filters.append('P')
        if job_types.get('temporary'):
            job_type_filters.append('T')
        if job_types.get('internship'):
            job_type_filters.append('I')
        if job_types.get('other'):
            job_type_filters.append('O')
        if job_types.get('volunteer'):
            job_type_filters.append('V')
        
        if job_type_filters:
            url_parts.append(f"f_JT={','.join(job_type_filters)}")
        
        # Date filter
        date_posted = parameters.get('date', {})
        if date_posted.get('all time'):
            pass  # No filter needed
        elif date_posted.get('month'):
            url_parts.append("f_TPR=r2592000")
        elif date_posted.get('week'):
            url_parts.append("f_TPR=r604800")
        elif date_posted.get('24 hours'):
            url_parts.append("f_TPR=r86400")
        
        # Distance
        distance = parameters.get('distance', 25)
        if distance != 25:  # 25 is default
            url_parts.append(f"distance={distance}")
        
        # Easy Apply filter
        url_parts.append("f_AL=true")
        
        base_url = "?" + "&".join(url_parts) if url_parts else ""
        return base_url
    
    def print_ai_stats(self):
        """Print AI usage statistics"""
        total_attempts = self.ai_success_count + self.ai_failure_count
        if total_attempts > 0:
            success_rate = (self.ai_success_count / total_attempts) * 100
            logger.info(f"🤖 AI Statistics:")
            logger.info(f"   ✅ Successful applications: {self.ai_success_count}")
            logger.info(f"   ❌ Failed applications: {self.ai_failure_count}")
            logger.info(f"   📊 Success rate: {success_rate:.1f}%")
        else:
            logger.info("🤖 No AI applications attempted")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.page:
                await self.page.close()
                logger.info("📄 Page closed")
            
            if self.context:
                await self.context.close()
                logger.info("🌐 Browser context closed")
            
            if self.browser:
                await self.browser.close()
                logger.info("🎭 Browser closed")
            
            if self.playwright:
                await self.playwright.stop()
                logger.info("🎬 Playwright stopped")
                
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")


# Helper function for creating the bot
def create_playwright_bot(parameters: Dict[str, Any]) -> PlaywrightLinkedInBot:
    """Factory function to create a Playwright LinkedIn bot"""
    return PlaywrightLinkedInBot(parameters)


# Main execution function
async def main():
    """Main async function for running the bot"""
    import yaml
    
    # Load configuration
    with open("config.yaml", 'r') as stream:
        parameters = yaml.safe_load(stream)
    
    # Create and run bot
    bot = create_playwright_bot(parameters)
    
    try:
        # Initialize browser
        await bot.initialize_browser()
        
        # Login and start applying
        await bot.login()
        await bot.security_check()
        await bot.start_applying()
        
        # Print statistics
        bot.print_ai_stats()
        
    finally:
        # Clean up
        await bot.cleanup()


if __name__ == '__main__':
    asyncio.run(main())