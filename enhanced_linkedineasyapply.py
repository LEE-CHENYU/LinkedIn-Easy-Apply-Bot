#!/usr/bin/env python3
"""
Enhanced LinkedIn Easy Apply Bot with browser-use integration
This version uses AI to handle complex application forms intelligently
"""

import time
import random
import os
import asyncio
import logging
import traceback
from functools import wraps
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_use_integration import BrowserUseLinkedInBot, load_openai_api_key

# Import the original LinkedinEasyApply class
import sys
sys.path.append('.')
from linkedineasyapply import LinkedinEasyApply

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedLinkedInEasyApply(LinkedinEasyApply):
    """Enhanced LinkedIn Easy Apply bot with AI-powered form handling"""
    
    def __init__(self, parameters, driver):
        """Initialize enhanced bot with browser-use capabilities"""
        super().__init__(parameters, driver)
        
        # Initialize browser-use components
        self.use_ai_forms = parameters.get('useAIForms', True)
        self.form_handling_mode = parameters.get('formHandlingMode', 'hybrid')  # 'ai-only', 'hardcoded-only', 'hybrid'
        self.ai_timeout = parameters.get('aiTimeout', 120)  # AI timeout in seconds
        self.openai_api_key = None
        self.browser_use_bot = None
        self.ai_success_count = 0
        self.ai_failure_count = 0
        
        # Load API key
        try:
            self.openai_api_key = load_openai_api_key()
            logger.info("OpenAI API key loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load OpenAI API key: {str(e)}")
            logger.warning("AI form handling will be disabled")
            self.use_ai_forms = False
    
    async def initialize_ai_agent(self):
        """Initialize the AI agent for form handling"""
        if not self.use_ai_forms or not self.openai_api_key:
            return False
            
        try:
            # Create browser-use bot with current config
            config = {
                'personalInfo': getattr(self, 'personal_info', {}),
                'checkboxes': getattr(self, 'checkboxes', {}),
                'technology': getattr(self, 'technology', {}),
                'industry': getattr(self, 'industry', {}),
                'universityGpa': getattr(self, 'university_gpa', '3.7'),
                'languages': getattr(self, 'languages', {}),
            }
            
            self.browser_use_bot = BrowserUseLinkedInBot(config, self.openai_api_key)
            await self.browser_use_bot.initialize_browser_use()
            await self.browser_use_bot.sync_with_selenium(self.browser)
            
            logger.info("AI agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI agent: {str(e)}")
            self.use_ai_forms = False
            return False
    
    def apply_to_job_with_ai(self, job_title="Unknown", company="Unknown"):
        """Apply to job using AI for form handling"""
        
        try:
            print("      🔄 Setting up AI application process...")
            
            # Check if we have the necessary components
            if not self.openai_api_key:
                print("      ❌ No OpenAI API key available")
                return False
                
            # Handle async execution properly
            import nest_asyncio
            
            # Allow nested event loops (required for Jupyter/async environments)
            try:
                nest_asyncio.apply()
                print("      ✅ Applied nest_asyncio for event loop compatibility")
            except Exception as nest_error:
                print(f"      ⚠️  nest_asyncio apply failed: {str(nest_error)}")
            
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                print("      ✅ Created new event loop")
                
            # Define the async operation
            async def _async_apply():
                """Async wrapper for AI application"""
                try:
                    print("      🤖 Initializing AI agent...")
                    
                    # Initialize AI agent if not already done
                    if not self.browser_use_bot:
                        success = await self.initialize_ai_agent()
                        if not success:
                            print("      ❌ AI agent initialization failed")
                            return False
                    
                    print(f"      🎯 AI applying to: {job_title} at {company}")
                    
                    # Use AI to handle the application with timeout
                    try:
                        success = await asyncio.wait_for(
                            self.browser_use_bot.handle_application_popup(job_title, company),
                            timeout=self.ai_timeout  # Configurable timeout for AI application
                        )
                        
                        if success:
                            self.ai_success_count += 1
                            print(f"      ✅ AI successfully completed application")
                            return True
                        else:
                            self.ai_failure_count += 1
                            print(f"      ❌ AI application returned False")
                            return False
                            
                    except asyncio.TimeoutError:
                        self.ai_failure_count += 1
                        print(f"      ❌ AI application timed out after {self.ai_timeout} seconds")
                        return False
                    
                except Exception as e:
                    self.ai_failure_count += 1
                    print(f"      ❌ AI application error: {str(e)}")
                    import traceback
                    print(f"      📋 Error traceback: {traceback.format_exc()}")
                    return False
            
            # Execute the async function
            try:
                if loop.is_running():
                    print("      ⚠️  Event loop already running, using create_task...")
                    # Create a task and wait for it
                    task = loop.create_task(_async_apply())
                    # Use a timeout to prevent hanging
                    return asyncio.run_coroutine_threadsafe(task, loop).result(timeout=150)
                else:
                    print("      ✅ Event loop available, running async operation...")
                    return loop.run_until_complete(_async_apply())
                    
            except Exception as execution_error:
                print(f"      ❌ Async execution error: {str(execution_error)}")
                
                # Final fallback: run in separate thread
                print("      🔄 Trying thread-based execution as last resort...")
                import concurrent.futures
                import threading
                
                def run_in_new_loop():
                    # Create completely new event loop in this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(_async_apply())
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    try:
                        return future.result(timeout=180)  # 3 minute total timeout
                    except concurrent.futures.TimeoutError:
                        print("      ❌ Thread execution timed out")
                        return False
                        
        except Exception as e:
            self.ai_failure_count += 1
            print(f"      💥 Critical AI application error: {str(e)}")
            return False
    
    def apply_to_job(self, job_title="Unknown", company="Unknown"):
        """Enhanced apply_to_job with AI integration and fallback"""
        
        # Debug folder will be created only if application fails
        debug_folder = None
        easy_apply_button = None

        # Use smart element finder for Easy Apply button
        easy_apply_selectors = [
            (By.CLASS_NAME, 'jobs-apply-button'),
            (By.CSS_SELECTOR, "button[aria-label*='Easy Apply']"),
            (By.CSS_SELECTOR, "button.jobs-apply-button"),
            (By.CSS_SELECTOR, "button[class*='jobs-apply']")
        ]
        
        easy_apply_button = self.smart_find_element(easy_apply_selectors, timeout=5)
        
        if not easy_apply_button:
            print("Could not find Easy Apply button")
            return False

        try:
            job_description_area = self.browser.find_element(By.CLASS_NAME, "jobs-search__job-details--container")
            self.scroll_slow(job_description_area, end=1600)
            self.scroll_slow(job_description_area, end=1600, step=400, reverse=True)
        except:
            pass

        print(f"📋 Applying to job: {job_title} at {company}")
        print(f"🤖 AI form handling: {'Enabled' if self.use_ai_forms else 'Disabled'}")
        
        easy_apply_button.click()
        
        # Wait for modal to appear
        time.sleep(2 * self.sleep_multiplier)
        
        print("📱 Application modal opened")
        
        # Ensure optimal viewport for form processing
        print("🔧 Optimizing browser viewport for form visibility...")
        self.ensure_optimal_viewport()

        # Determine form handling approach based on mode
        print(f"🔧 Form handling mode: {self.form_handling_mode}")
        
        if self.form_handling_mode == 'hardcoded-only':
            print("🔧 Using hardcoded-only form handling...")
            return self._manual_apply_to_job(job_title, company, debug_folder)
        
        elif self.form_handling_mode == 'ai-only':
            print("🤖 Using AI-only form handling...")
            if not self.use_ai_forms or not self.openai_api_key:
                print("❌ AI-only mode requested but AI is not available")
                raise Exception("AI-only mode requested but AI is not configured properly")
            
            ai_success = self.apply_to_job_with_ai(job_title, company)
            if ai_success:
                print(f"✅ AI successfully completed application for {job_title}")
                return True
            else:
                print("❌ AI application failed in AI-only mode")
                raise Exception("AI application failed and no fallback allowed in AI-only mode")
        
        else:  # hybrid mode (default)
            print("🔄 Using hybrid form handling (AI with hardcoded fallback)...")
            
            # Try AI first if available
            if self.use_ai_forms and self.openai_api_key:
                try:
                    print("🤖 Attempting AI-powered application...")
                    print(f"   - Job: {job_title}")
                    print(f"   - Company: {company}")
                    print(f"   - AI timeout: {self.ai_timeout}s")
                    print(f"   - Using OpenAI API key: {'✅ Available' if self.openai_api_key else '❌ Missing'}")
                    
                    ai_success = self.apply_to_job_with_ai(job_title, company)
                    
                    if ai_success:
                        print(f"✅ AI successfully completed application for {job_title}")
                        return True
                    else:
                        print("❌ AI application failed, falling back to enhanced hardcoded method...")
                        print("   - This may be due to complex forms or AI limitations")
                        
                except Exception as e:
                    print(f"❌ AI application error: {str(e)}")
                    print("   - Falling back to enhanced hardcoded method...")
                    import traceback
                    print(f"   - Error details: {traceback.format_exc()}")
            else:
                print("⚠️  AI not available, using enhanced hardcoded method")
            
            # Fallback to enhanced hardcoded method
            print("🔧 Using enhanced hardcoded form handling...")
            return self._manual_apply_to_job(job_title, company, debug_folder)
    
    def _manual_apply_to_job(self, job_title, company, debug_folder):
        """Original manual apply_to_job method as fallback"""
        
        print(f"🔧 Starting manual application process for: {job_title}")
        print(f"   📊 Current page URL: {self.browser.current_url}")
        print(f"   📊 Page title: {self.browser.title}")
        
        # Check initial modal state
        try:
            modal_elements = self.browser.find_elements(By.CSS_SELECTOR, ".artdeco-modal")
            print(f"   📊 Found {len(modal_elements)} modal elements on page")
            if modal_elements:
                modal_title = self.browser.find_element(By.CSS_SELECTOR, ".artdeco-modal__header h1, .artdeco-modal__header .t-24").text
                print(f"   📊 Modal title: '{modal_title}'")
        except:
            print("   📊 No modal found or error reading modal")
        
        button_text = ""
        submit_application_text = 'submit application'
        form_step_count = 0
        
        # Track page changes to detect if stuck
        previous_url = ""
        same_page_count = 0
        max_same_page_retries = 3
        
        print(f"🔧 Beginning form processing loop (max steps: {self.max_form_steps})")
        
        # Ensure viewport is optimized before starting form processing
        self.ensure_optimal_viewport()
        
        while submit_application_text not in button_text.lower() and form_step_count < self.max_form_steps:
            form_step_count += 1
            current_url = self.browser.current_url
            
            print(f"📝 Processing form step {form_step_count}/{self.max_form_steps}")
            print(f"   📊 Current URL: {current_url}")
            
            # Check if we're stuck on the same page
            if current_url == previous_url:
                same_page_count += 1
                print(f"   ⚠️  Same page detected ({same_page_count}/{max_same_page_retries} times)")
                
                if same_page_count >= max_same_page_retries:
                    print(f"   💥 STUCK DETECTION: Been on same page {same_page_count} times!")
                    print(f"      URL: {current_url}")
                    print(f"      This usually means button clicking isn't working or validation errors persist")
                    
                    # Try to find and analyze the current state
                    try:
                        # Check if there are validation errors
                        page_source = self.browser.page_source.lower()
                        if 'please make a selection' in page_source:
                            print(f"      🎯 CAUSE: Radio button validation errors detected")
                            print(f"      🔧 SOLUTION: Running emergency radio button fix...")
                            self.fix_unselected_radio_buttons()
                        elif 'please enter a valid answer' in page_source:
                            print(f"      🎯 CAUSE: Text field validation errors detected")
                        elif 'file is required' in page_source:
                            print(f"      🎯 CAUSE: File upload requirements detected")
                        else:
                            print(f"      🎯 CAUSE: Unknown - no obvious validation errors")
                    except:
                        print(f"      ❌ Could not analyze stuck cause")
                    
                    # Break out of the stuck loop
                    print(f"      🚨 Aborting to prevent infinite loop")
                    break
            else:
                same_page_count = 0  # Reset counter when page changes
                previous_url = current_url
            
            # Detailed page content analysis
            page_source = self.browser.page_source.lower()
            print(f"   📊 Page source length: {len(page_source)} characters")
            
            # Check for specific form elements and content
            if 'please make a selection' in page_source:
                print("⚠️  Detected radio button validation errors on current page")
                # Count how many radio button errors
                radio_errors = page_source.count('please make a selection')
                print(f"   📊 Number of radio button validation errors: {radio_errors}")
                
            if 'additional questions' in page_source:
                print("📋 Found 'Additional Questions' section")
                
            if 'work authorization' in page_source:
                print("🔐 Found work authorization questions")
                
            if 'years of experience' in page_source:
                print("🎯 Found experience-related questions")
                
            if 'upload' in page_source and ('resume' in page_source or 'cv' in page_source):
                print("📁 Found file upload requirements")
                
            if 'cover letter' in page_source:
                print("📄 Found cover letter requirements")
                
            # Check for form inputs
            try:
                text_inputs = self.browser.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel'], textarea")
                select_elements = self.browser.find_elements(By.CSS_SELECTOR, "select")
                radio_buttons = self.browser.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                checkboxes = self.browser.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                
                print(f"   📊 Form elements found:")
                print(f"      - Text inputs: {len(text_inputs)}")
                print(f"      - Select dropdowns: {len(select_elements)}")
                print(f"      - Radio buttons: {len(radio_buttons)}")
                print(f"      - Checkboxes: {len(checkboxes)}")
                
                # Check if any required fields are empty
                empty_required = 0
                for input_elem in text_inputs:
                    if input_elem.get_attribute('required') and not input_elem.get_attribute('value'):
                        empty_required += 1
                
                if empty_required > 0:
                    print(f"   ⚠️  Found {empty_required} empty required text fields")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing form elements: {str(e)}")
            
            retries = 3
            while retries > 0:
                try:
                    print(f"   🔄 Attempt {4 - retries}/3 - Starting form fill process")
                    
                    # Use enhanced fill_up method with comprehensive handling
                    print("   📝 Using enhanced form filling method...")
                    self.enhanced_fill_up()
                    print("   ✅ Enhanced fill_up completed")
                    
                    # Use smart element finder for next button
                    print("   🔍 Looking for next/submit button...")
                    next_button_selectors = [
                        # Priority selectors - most specific first
                        (By.CSS_SELECTOR, "button[data-easy-apply-next-button]"),  # LinkedIn's specific next button
                        (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
                        (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
                        (By.CSS_SELECTOR, "button[aria-label*='Submit']"),
                        # Generic selectors with exclusions
                        (By.CSS_SELECTOR, "button.artdeco-button--primary:not([aria-label*='Back'])"),
                        (By.CSS_SELECTOR, "button[aria-label*='Continue']:not([aria-label*='Back'])"),
                        (By.CSS_SELECTOR, "button[aria-label*='Review']:not([aria-label*='Back'])"),
                        (By.CSS_SELECTOR, "button.artdeco-button--primary"),
                    ]
                    
                    # First try to find the next button with improved logic
                    next_button = None
                    for selector_by, selector_value in next_button_selectors:
                        try:
                            buttons = self.browser.find_elements(selector_by, selector_value)
                            if buttons:
                                # Filter out back buttons and select the best candidate
                                valid_buttons = []
                                for btn in buttons:
                                    aria_label = btn.get_attribute('aria-label') or ""
                                    button_text = btn.text.lower()
                                    
                                    # Skip back buttons
                                    if ('back' in aria_label.lower() or 'back' in button_text):
                                        continue
                                        
                                    # Prioritize buttons with next/continue/submit keywords
                                    if any(keyword in aria_label.lower() or keyword in button_text 
                                           for keyword in ['next', 'continue', 'submit', 'review']):
                                        valid_buttons.append((btn, 2))  # High priority
                                    elif 'artdeco-button--primary' in btn.get_attribute('class'):
                                        valid_buttons.append((btn, 1))  # Medium priority
                                    else:
                                        valid_buttons.append((btn, 0))  # Low priority
                                
                                if valid_buttons:
                                    # Sort by priority and take the highest
                                    valid_buttons.sort(key=lambda x: x[1], reverse=True)
                                    next_button = valid_buttons[0][0]
                                    print(f"   ✅ Found button using selector: {selector_value}")
                                    break
                        except:
                            continue
                    
                    # Fallback: manual button analysis if smart selection fails
                    if not next_button:
                        print("   🔍 Smart selection failed, trying specific container pattern...")
                        
                        # Look for the specific container pattern you mentioned
                        try:
                            container = self.browser.find_element(By.CSS_SELECTOR, "div.display-flex.justify-flex-end.ph5.pv4")
                            if container:
                                print("   ✅ Found LinkedIn button container")
                                buttons_in_container = container.find_elements(By.CSS_SELECTOR, "button")
                                
                                for btn in buttons_in_container:
                                    aria_label = btn.get_attribute('aria-label') or ""
                                    button_text = btn.text.strip().lower()
                                    
                                    print(f"      Container button: '{button_text}' | aria: '{aria_label}'")
                                    
                                    # Select the Next/Continue button, not the Back button
                                    if ('continue to next step' in aria_label.lower() or 
                                        'next' in button_text or
                                        'continue' in button_text or
                                        'artdeco-button--primary' in btn.get_attribute('class')):
                                        
                                        # Make sure it's not a back button
                                        if not ('back' in aria_label.lower() or 'back' in button_text):
                                            next_button = btn
                                            print(f"   ✅ Selected button from container: '{button_text}'")
                                            break
                        except:
                            print("   ⚠️  Container pattern not found")
                        
                        # Final fallback: comprehensive button analysis
                        if not next_button:
                            print("   🔍 Container selection failed, analyzing all buttons...")
                            all_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button")
                            next_button = self.analyze_and_select_best_button(all_buttons)
                    
                    if not next_button:
                        print("   ❌ Could not find next button using any selector")
                        # Try to find ANY buttons on the page for debugging
                        all_buttons = self.browser.find_elements(By.TAG_NAME, "button")
                        print(f"   📊 Found {len(all_buttons)} total buttons on page")
                        for i, btn in enumerate(all_buttons[:5]):  # Show first 5 buttons
                            try:
                                btn_text = btn.text.strip()
                                btn_classes = btn.get_attribute('class')
                                btn_aria = btn.get_attribute('aria-label')
                                print(f"      Button {i+1}: text='{btn_text}', classes='{btn_classes}', aria-label='{btn_aria}'")
                            except:
                                print(f"      Button {i+1}: Error reading button properties")
                        raise Exception("Could not find next button")
                    
                    button_text = next_button.text.lower().strip()
                    button_aria = next_button.get_attribute('aria-label') or ""
                    button_classes = next_button.get_attribute('class') or ""
                    
                    print(f"   ✅ Found next button:")
                    print(f"      Text: '{button_text}'")
                    print(f"      Aria-label: '{button_aria}'")
                    print(f"      Classes: '{button_classes}'")
                    print(f"      Is enabled: {next_button.is_enabled()}")
                    print(f"      Is displayed: {next_button.is_displayed()}")
                    
                    if submit_application_text in button_text:
                        print("   🎯 This is the final submit button!")
                        try:
                            print("   📤 Attempting to unfollow company before submission...")
                            self.unfollow()
                            print("   ✅ Unfollowed company successfully")
                        except Exception as e:
                            print(f"   ⚠️  Failed to unfollow company: {str(e)}")
                    
                    print(f"   ⏱️  Waiting {1 * self.sleep_multiplier}-{1.5 * self.sleep_multiplier}s before clicking...")
                    time.sleep(random.uniform(1, 1.5) * self.sleep_multiplier)
                    
                    # Try clicking the button with multiple methods
                    print("   🖱️  Attempting to click button...")
                    button_clicked = False
                    
                    try:
                        # Wait for button to be clickable
                        print("      Method 1: WebDriverWait + click()")
                        wait = WebDriverWait(self.browser, 10)
                        clickable_button = wait.until(EC.element_to_be_clickable(next_button))
                        clickable_button.click()
                        button_clicked = True
                        print("      ✅ Button clicked successfully with method 1")
                    except Exception as e1:
                        print(f"      ❌ Method 1 failed: {str(e1)}")
                        try:
                            # Try JavaScript click as fallback
                            print("      Method 2: JavaScript click()")
                            self.browser.execute_script("arguments[0].click();", next_button)
                            button_clicked = True
                            print("      ✅ Button clicked successfully with method 2 (JavaScript)")
                        except Exception as e2:
                            print(f"      ❌ Method 2 failed: {str(e2)}")
                            try:
                                # Try scrolling to button and clicking
                                print("      Method 3: Scroll + click()")
                                self.browser.execute_script("arguments[0].scrollIntoView();", next_button)
                                time.sleep(0.5)
                                next_button.click()
                                button_clicked = True
                                print("      ✅ Button clicked successfully with method 3 (scroll + click)")
                            except Exception as e3:
                                print(f"      ❌ Method 3 failed: {str(e3)}")
                                print(f"   ❌ All click methods failed!")
                                raise Exception(f"Could not click next button after trying all methods: {str(e3)}")
                    
                    if button_clicked:
                        print(f"   ⏱️  Waiting {2 * self.sleep_multiplier}-{3 * self.sleep_multiplier}s for page to load...")
                        time.sleep(random.uniform(2, 3) * self.sleep_multiplier)
                        
                        print("   📊 Checking new page state after button click...")
                        print(f"      New URL: {self.browser.current_url}")
                        print(f"      New page title: {self.browser.title}")

                    # Check for validation errors including radio button errors
                    print("   🔍 Checking for validation errors...")
                    page_source_lower = self.browser.page_source.lower()
                    
                    validation_errors = []
                    if 'please enter a valid answer' in page_source_lower:
                        validation_errors.append("Invalid answer error")
                    if 'file is required' in page_source_lower:
                        validation_errors.append("Required file error")
                    if 'please make a selection' in page_source_lower:
                        validation_errors.append("Radio button selection error")
                    if 'field is required' in page_source_lower:
                        validation_errors.append("Required field error")
                    if 'invalid format' in page_source_lower:
                        validation_errors.append("Invalid format error")
                        
                    if validation_errors:
                        print(f"   ⚠️  Found validation errors: {', '.join(validation_errors)}")
                        retries -= 1
                        print(f"   🔄 Retrying application, attempts left: {retries}")
                        
                        # If we have radio button errors, log them specifically
                        if 'please make a selection' in page_source_lower:
                            print("   📋 Radio button validation error details:")
                            # Try to find specific radio button groups with errors
                            try:
                                error_elements = self.browser.find_elements(By.XPATH, "//*[contains(text(), 'Please make a selection')]")
                                print(f"      Found {len(error_elements)} 'Please make a selection' error messages")
                                
                                for i, error_elem in enumerate(error_elements):
                                    try:
                                        # Find the parent fieldset or form group
                                        parent = error_elem.find_element(By.XPATH, "./ancestor::fieldset | ./ancestor::div[contains(@class, 'form-group')] | ./ancestor::div[contains(@class, 'jobs-easy-apply-form-section__grouping')]")
                                        question_text = parent.find_element(By.CSS_SELECTOR, "legend, label, .fb-form-element-label, .fb-form-element h3").text
                                        print(f"      Error {i+1}: '{question_text}'")
                                        
                                        # Try to find the radio buttons in this group
                                        radio_buttons = parent.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                                        print(f"         - Found {len(radio_buttons)} radio buttons in this group")
                                        
                                        # Check which ones are selected
                                        selected_count = 0
                                        for radio in radio_buttons:
                                            if radio.is_selected():
                                                selected_count += 1
                                        print(f"         - {selected_count} radio buttons are selected")
                                        
                                        if selected_count == 0:
                                            print("         - ⚠️  NO radio buttons selected in this group!")
                                            
                                            # Try to manually select one as a fallback
                                            if radio_buttons:
                                                print("         - 🔧 Attempting emergency radio button selection...")
                                                try:
                                                    # Try to select the first or last radio button
                                                    radio_buttons[0].click()
                                                    print(f"         - ✅ Selected first radio button as fallback")
                                                except Exception as radio_error:
                                                    print(f"         - ❌ Failed to select radio button: {str(radio_error)}")
                                        
                                    except Exception as analysis_error:
                                        print(f"      Error {i+1}: Could not determine question details - {str(analysis_error)}")
                            except Exception as outer_error:
                                print(f"      Could not analyze specific radio button errors - {str(outer_error)}")
                                
                            # Also try a different approach - find all unselected required radio button groups
                            print("   🔍 Additional analysis - looking for unselected required radio groups...")
                            try:
                                all_radio_groups = self.browser.find_elements(By.CSS_SELECTOR, "fieldset, .jobs-easy-apply-form-section__grouping")
                                for i, group in enumerate(all_radio_groups):
                                    try:
                                        radios_in_group = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                                        if len(radios_in_group) > 0:
                                            selected_in_group = [r for r in radios_in_group if r.is_selected()]
                                            if len(selected_in_group) == 0:
                                                group_text = group.text[:100]  # First 100 chars
                                                print(f"      Group {i+1}: No selection in '{group_text}' ({len(radios_in_group)} options)")
                                    except:
                                        pass
                            except Exception as group_error:
                                print(f"      Group analysis failed: {str(group_error)}")
                        
                        # Create debug folder only when needed and debug mode is enabled
                        if self.debug_mode and debug_folder is None:
                            debug_folder = self.create_debug_folder(job_title, company)
                            print(f"   📁 Created debug folder: {debug_folder}")
                        
                        # Save page source when retry is needed (only in debug mode)
                        if self.debug_mode and debug_folder:
                            retry_count = 3 - retries
                            filename = f'{debug_folder}/failed_application_retry_{retry_count}.html'
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(self.browser.page_source)
                            print(f"   💾 Saved page source to {filename}")
                        
                        print("   ⏭️  Continuing to next retry attempt...")

                    else:
                        print("   ✅ No validation errors found - proceeding to next step")
                        break
                except Exception as retry_error:
                    print(f"   ❌ Exception occurred in retry loop: {str(retry_error)}")
                    import traceback
                    traceback.print_exc()
                    raise Exception(f"Failed to apply to job during form step {form_step_count}: {str(retry_error)}")
                    
            if retries == 0:
                print(f"   💥 All retries exhausted at form step {form_step_count}")
                print(f"      Final page URL: {self.browser.current_url}")
                print(f"      Final page title: {self.browser.title}")
                
                # Create debug folder only when needed and debug mode is enabled
                if self.debug_mode and debug_folder is None:
                    debug_folder = self.create_debug_folder(job_title, company)
                    print(f"   📁 Created debug folder: {debug_folder}")
                
                # Save the final failed page (only in debug mode)
                if self.debug_mode and debug_folder:
                    filename = f'{debug_folder}/failed_application_final.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.browser.page_source)
                    print(f"   💾 Saved final failed page to {filename}")
                    
                    # Also save a summary of the failure
                    summary_file = f'{debug_folder}/failure_summary.txt'
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(f"Application Failure Summary\n")
                        f.write(f"=========================\n")
                        f.write(f"Job Title: {job_title}\n")
                        f.write(f"Company: {company}\n")
                        f.write(f"Failed at form step: {form_step_count}\n")
                        f.write(f"Final URL: {self.browser.current_url}\n")
                        f.write(f"Final page title: {self.browser.title}\n")
                        f.write(f"Reason: All 3 retry attempts exhausted\n")
                    print(f"   📝 Saved failure summary to {summary_file}")
                
                traceback.print_exc()
                try:
                    self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
                    time.sleep(random.uniform(2, 3) * self.sleep_multiplier)
                    self.browser.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[1].click()
                    time.sleep(random.uniform(2, 3) * self.sleep_multiplier)
                except Exception as e:
                    print(f"Error closing modal: {str(e)}")
                raise Exception("Failed to apply to job!")
        
        # Check if we hit the form step limit
        if form_step_count >= self.max_form_steps:
            print(f"💥 Application exceeded maximum form steps ({self.max_form_steps})")
            print(f"   📊 Final application state:")
            print(f"      Current URL: {self.browser.current_url}")
            print(f"      Page title: {self.browser.title}")
            print(f"      Last button text: '{button_text}'")
            
            # Create debug folder only when needed and debug mode is enabled
            if self.debug_mode and debug_folder is None:
                debug_folder = self.create_debug_folder(job_title, company)
                print(f"   📁 Created debug folder: {debug_folder}")
            
            # Save the page where we got stuck (only in debug mode)
            if self.debug_mode and debug_folder:
                filename = f'{debug_folder}/stuck_at_step_{form_step_count}.html'
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.browser.page_source)
                print(f"   💾 Saved stuck page to {filename}")
                
                # Save detailed analysis
                analysis_file = f'{debug_folder}/step_limit_analysis.txt'
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    f.write(f"Step Limit Exceeded Analysis\n")
                    f.write(f"==========================\n")
                    f.write(f"Job Title: {job_title}\n")
                    f.write(f"Company: {company}\n")
                    f.write(f"Steps processed: {form_step_count}\n")
                    f.write(f"Max steps allowed: {self.max_form_steps}\n")
                    f.write(f"Final URL: {self.browser.current_url}\n")
                    f.write(f"Final page title: {self.browser.title}\n")
                    f.write(f"Last button text: '{button_text}'\n")
                    f.write(f"Reason: Exceeded maximum form steps - likely stuck in loop\n")
                print(f"   📝 Saved step limit analysis to {analysis_file}")
            
            raise Exception(f"Application form exceeded maximum steps ({self.max_form_steps})")

        print("🎉 Application form completed successfully!")
        print(f"   📊 Total form steps processed: {form_step_count}")
        print(f"   📊 Final URL: {self.browser.current_url}")
        
        print("⏱️  Waiting before closing confirmation modal...")
        time.sleep(random.uniform(2, 3) * self.sleep_multiplier)
        
        closed_notification = False
        print("🔍 Looking for confirmation modal to close...")
        
        try:
            modal_dismiss = self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss')
            modal_dismiss.click()
            closed_notification = True
            print("✅ Closed main modal successfully")
        except Exception as e:
            print(f"⚠️  Could not find/click main modal dismiss button: {str(e)}")
            
        try:
            toast_dismiss = self.browser.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss')
            toast_dismiss.click()
            closed_notification = True
            print("✅ Closed toast notification successfully")
        except Exception as e:
            print(f"⚠️  Could not find/click toast dismiss button: {str(e)}")
            
        # Try additional methods to close notifications
        if not closed_notification:
            print("🔍 Trying additional methods to close notifications...")
            try:
                # Try ESC key
                from selenium.webdriver.common.keys import Keys
                self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                closed_notification = True
                print("✅ Used ESC key to close modal")
            except Exception as e:
                print(f"⚠️  ESC key method failed: {str(e)}")
            
        print("⏱️  Final wait before returning...")
        time.sleep(random.uniform(1, 2) * self.sleep_multiplier)

        if closed_notification is False:
            print("❌ Could not close confirmation window using any method")
            print(f"   📊 Current page elements:")
            try:
                modals = self.browser.find_elements(By.CSS_SELECTOR, ".artdeco-modal")
                toasts = self.browser.find_elements(By.CSS_SELECTOR, ".artdeco-toast-item")
                print(f"      Modals found: {len(modals)}")
                print(f"      Toasts found: {len(toasts)}")
            except:
                print("      Could not analyze page elements")
            raise Exception("Could not close the applied confirmation window!")

        print("✅ Application completed and confirmed successfully!")
        return True
    
    def fix_unselected_radio_buttons(self):
        """Proactive method to find and fix unselected required radio buttons"""
        try:
            print("      🔧 Checking for unselected required radio button groups...")
            fixed_count = 0
            
            # Find all potential radio button containers
            containers = self.browser.find_elements(By.CSS_SELECTOR, 
                "fieldset, .jobs-easy-apply-form-section__grouping, .artdeco-card, .jobs-easy-apply-form-element")
            
            for i, container in enumerate(containers):
                try:
                    # Check if this container has radio buttons
                    radio_buttons = container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    
                    if len(radio_buttons) > 0:
                        # Check if any are selected
                        selected_radios = [r for r in radio_buttons if r.is_selected()]
                        
                        if len(selected_radios) == 0:
                            # No radio button selected in this group
                            try:
                                # Get question text for context
                                question_elements = container.find_elements(By.CSS_SELECTOR, 
                                    "legend, label, .fb-form-element-label, h3, h4, span[class*='label']")
                                question_text = ""
                                if question_elements:
                                    question_text = question_elements[0].text[:80]  # First 80 chars
                                
                                print(f"         🎯 Found unselected radio group: '{question_text}'")
                                print(f"            - {len(radio_buttons)} radio options available")
                                
                                # Smart selection based on question type
                                selected = self.smart_radio_selection(radio_buttons, question_text.lower())
                                
                                if selected:
                                    fixed_count += 1
                                    print(f"            - ✅ Smart selection made")
                                else:
                                    # Fallback: select first available option
                                    try:
                                        radio_buttons[0].click()
                                        fixed_count += 1
                                        print(f"            - ✅ Selected first option as fallback")
                                    except:
                                        print(f"            - ❌ Could not select any option")
                                        
                            except Exception as selection_error:
                                print(f"            - ❌ Error during selection: {str(selection_error)}")
                                
                except Exception as container_error:
                    continue  # Skip problematic containers
                    
            if fixed_count > 0:
                print(f"      ✅ Fixed {fixed_count} unselected radio button groups")
            else:
                print(f"      ✅ All radio button groups appear to be properly selected")
                
        except Exception as e:
            print(f"      ❌ Error in radio button validation: {str(e)}")
    
    def smart_radio_selection(self, radio_buttons, question_text):
        """Smart radio button selection based on question context"""
        try:
            # Get radio button labels
            radio_labels = []
            for radio in radio_buttons:
                try:
                    # Try different ways to get the label
                    label_text = ""
                    
                    # Method 1: Associated label element
                    radio_id = radio.get_attribute('id')
                    if radio_id:
                        try:
                            label_elem = self.browser.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                            label_text = label_elem.text
                        except:
                            pass
                    
                    # Method 2: Parent element text
                    if not label_text:
                        parent = radio.find_element(By.XPATH, "..")
                        label_text = parent.text.replace('\n', ' ').strip()
                    
                    # Method 3: Following sibling text
                    if not label_text:
                        try:
                            sibling = radio.find_element(By.XPATH, "./following-sibling::*[1]")
                            label_text = sibling.text
                        except:
                            pass
                    
                    radio_labels.append((radio, label_text.lower().strip()))
                    
                except:
                    radio_labels.append((radio, ""))
            
            print(f"            Radio options: {[label for _, label in radio_labels]}")
            
            # Smart selection logic based on question type
            selected_radio = None
            
            # Work authorization questions
            if any(keyword in question_text for keyword in ['authorized', 'authorised', 'legally', 'work in', 'employment']):
                # Look for "yes" or positive answers
                for radio, label in radio_labels:
                    if any(keyword in label for keyword in ['yes', 'authorized', 'authorised', 'eligible']):
                        selected_radio = radio
                        break
                        
            # Visa sponsorship questions
            elif any(keyword in question_text for keyword in ['sponsor', 'visa', 'h1b', 'require']):
                # Look for "no" answers for visa sponsorship
                for radio, label in radio_labels:
                    if any(keyword in label for keyword in ['no', 'not required', 'don\'t']):
                        selected_radio = radio
                        break
                        
            # Driver's license questions
            elif any(keyword in question_text for keyword in ['driver', 'license', 'licence']):
                # Look for "yes"
                for radio, label in radio_labels:
                    if 'yes' in label:
                        selected_radio = radio
                        break
                        
            # EEO/demographic questions (prefer not to answer)
            elif any(keyword in question_text for keyword in ['gender', 'race', 'veteran', 'disability', 'ethnicity', 'sexual']):
                # Look for "prefer not to answer" or similar
                for radio, label in radio_labels:
                    if any(keyword in label for keyword in ['prefer', 'decline', 'don\'t', 'not specified', 'none']):
                        selected_radio = radio
                        break
                # If not found, select last option
                if not selected_radio and radio_labels:
                    selected_radio = radio_labels[-1][0]
                    
            # Years of experience - default to first option (usually lowest)
            elif any(keyword in question_text for keyword in ['year', 'experience', 'how many']):
                if radio_labels:
                    selected_radio = radio_labels[0][0]  # Usually first = lowest experience
                    
            # Default: try to select first "yes" or first option
            if not selected_radio:
                for radio, label in radio_labels:
                    if 'yes' in label:
                        selected_radio = radio
                        break
                if not selected_radio and radio_labels:
                    selected_radio = radio_labels[0][0]
            
            # Make the selection
            if selected_radio:
                selected_radio.click()
                return True
                
        except Exception as e:
            print(f"            Smart selection error: {str(e)}")
            
        return False
    
    def enhanced_fill_up(self):
        """Enhanced version of fill_up with better new LinkedIn structure handling"""
        try:
            print("      🔧 Starting enhanced form filling...")
            
            # First, try the original fill_up method
            print("      📝 Calling original fill_up method...")
            self.fill_up()
            print("      ✅ Original fill_up completed")
            
            # Then, do additional comprehensive form handling
            print("      🔍 Performing comprehensive form analysis...")
            
            # Handle any remaining radio button issues
            self.handle_radio_buttons_comprehensive()
            
            # Handle any text inputs that might have been missed
            self.handle_text_inputs_comprehensive()
            
            # Handle dropdowns
            self.handle_dropdowns_comprehensive()
            
            print("      ✅ Enhanced form filling completed")
            
        except Exception as e:
            print(f"      ❌ Error in enhanced_fill_up: {str(e)}")
            
    def handle_radio_buttons_comprehensive(self):
        """Comprehensive radio button handling for modern LinkedIn forms"""
        try:
            print("         🔘 Analyzing all radio button groups...")
            
            # Find all radio button containers using multiple selectors
            all_containers = []
            
            # Method 1: Traditional structure
            containers_old = self.browser.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
            all_containers.extend(containers_old)
            
            # Method 2: New artdeco structure
            containers_new = self.browser.find_elements(By.CSS_SELECTOR, '.artdeco-card, fieldset, [data-test-form-element]')
            all_containers.extend(containers_new)
            
            # Method 3: Generic form containers
            containers_generic = self.browser.find_elements(By.CSS_SELECTOR, 'div[class*="form"], div[class*="question"], div[class*="group"]')
            all_containers.extend(containers_generic)
            
            # Remove duplicates
            seen_containers = set()
            unique_containers = []
            for container in all_containers:
                try:
                    # Use element location as unique identifier
                    location_id = f"{container.location['x']}_{container.location['y']}"
                    if location_id not in seen_containers:
                        seen_containers.add(location_id)
                        unique_containers.append(container)
                except:
                    continue
            
            print(f"         📊 Found {len(unique_containers)} unique form containers to analyze")
            
            processed_groups = 0
            for i, container in enumerate(unique_containers):
                try:
                    # Find radio buttons in this container
                    radio_buttons = container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    
                    if len(radio_buttons) > 0:
                        # Check if any radio button in this group is selected
                        selected_radios = [r for r in radio_buttons if r.is_selected()]
                        
                        if len(selected_radios) == 0:
                            # This group needs attention
                            processed_groups += 1
                            
                            # Get question context
                            question_text = self.extract_question_text(container)
                            print(f"         🎯 Processing radio group {processed_groups}: '{question_text[:60]}...'")
                            
                            # Apply intelligent selection
                            success = self.intelligent_radio_selection(radio_buttons, question_text, container)
                            
                            if success:
                                print(f"         ✅ Successfully handled radio group {processed_groups}")
                            else:
                                print(f"         ⚠️  Could not handle radio group {processed_groups}")
                                
                except Exception as container_error:
                    continue
                    
            print(f"         ✅ Processed {processed_groups} radio button groups")
            
        except Exception as e:
            print(f"         ❌ Error in radio button comprehensive handling: {str(e)}")
    
    def handle_text_inputs_comprehensive(self):
        """Comprehensive text input handling for modern LinkedIn forms"""
        try:
            print("         📝 Analyzing all text input fields...")
            
            # Find all text inputs using multiple selectors
            all_inputs = []
            
            # Method 1: Artdeco inputs
            inputs_artdeco = self.browser.find_elements(By.CSS_SELECTOR, "input[class*='artdeco-text-input']")
            all_inputs.extend(inputs_artdeco)
            
            # Method 2: Standard text inputs
            inputs_standard = self.browser.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], input[type='email'], input[type='tel']")
            all_inputs.extend(inputs_standard)
            
            # Method 3: Textareas
            textareas = self.browser.find_elements(By.TAG_NAME, "textarea")
            all_inputs.extend(textareas)
            
            print(f"         📊 Found {len(all_inputs)} total input fields")
            
            filled_count = 0
            for input_field in all_inputs:
                try:
                    # Skip if already filled
                    current_value = input_field.get_attribute('value') or ''
                    if current_value.strip():
                        continue
                    
                    # Get question context
                    question_text = self.get_input_question_text(input_field)
                    
                    if question_text:
                        # Determine appropriate value
                        value = self.determine_input_value(question_text, input_field)
                        
                        if value is not None:
                            input_field.clear()
                            input_field.send_keys(str(value))
                            filled_count += 1
                            print(f"         ✅ Filled input: '{question_text[:40]}...' = '{value}'")
                            
                except Exception as input_error:
                    continue
                    
            print(f"         ✅ Filled {filled_count} text input fields")
            
        except Exception as e:
            print(f"         ❌ Error in text input comprehensive handling: {str(e)}")
    
    def handle_dropdowns_comprehensive(self):
        """Comprehensive dropdown handling for modern LinkedIn forms"""
        try:
            print("         🔽 Analyzing all dropdown fields...")
            
            # Find all select elements
            selects = self.browser.find_elements(By.TAG_NAME, "select")
            
            print(f"         📊 Found {len(selects)} dropdown fields")
            
            filled_count = 0
            for select in selects:
                try:
                    # Skip if already selected (not default)
                    from selenium.webdriver.support.ui import Select
                    select_obj = Select(select)
                    selected_option = select_obj.first_selected_option
                    
                    # Skip if it's not the first/default option
                    if selected_option != select_obj.options[0]:
                        continue
                    
                    # Get question context
                    question_text = self.get_input_question_text(select)
                    
                    if question_text:
                        # Determine appropriate selection
                        value = self.determine_dropdown_value(question_text, select_obj)
                        
                        if value is not None:
                            select_obj.select_by_visible_text(value)
                            filled_count += 1
                            print(f"         ✅ Selected dropdown: '{question_text[:40]}...' = '{value}'")
                            
                except Exception as select_error:
                    continue
                    
            print(f"         ✅ Filled {filled_count} dropdown fields")
            
        except Exception as e:
            print(f"         ❌ Error in dropdown comprehensive handling: {str(e)}")
    
    def extract_question_text(self, container):
        """Extract question text from a form container"""
        try:
            # Try multiple methods to get question text
            selectors = [
                "legend", 
                "label", 
                ".fb-form-element-label", 
                "h3", 
                "h4", 
                "h2",
                "span[class*='label']",
                ".artdeco-text-input--label",
                "[data-test-form-element-label]"
            ]
            
            for selector in selectors:
                try:
                    element = container.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and len(text) > 3:  # Minimum meaningful length
                        return text
                except:
                    continue
            
            # Fallback: use container text (cleaned)
            container_text = container.text.replace('\n', ' ').strip()
            if container_text and len(container_text) > 3:
                return container_text[:200]  # Limit length
                
            return "Unknown question"
            
        except:
            return "Unknown question"
    
    def get_input_question_text(self, input_element):
        """Get question text for an input element"""
        try:
            # Method 1: Associated label
            input_id = input_element.get_attribute('id')
            if input_id:
                try:
                    label = self.browser.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    return label.text.strip()
                except:
                    pass
            
            # Method 2: Placeholder
            placeholder = input_element.get_attribute('placeholder')
            if placeholder and len(placeholder) > 3:
                return placeholder.strip()
            
            # Method 3: aria-label
            aria_label = input_element.get_attribute('aria-label')
            if aria_label and len(aria_label) > 3:
                return aria_label.strip()
            
            # Method 4: Parent element text
            try:
                parent = input_element.find_element(By.XPATH, "..")
                parent_text = parent.text.replace('\n', ' ').strip()
                if parent_text and len(parent_text) > 3:
                    return parent_text[:100]
            except:
                pass
            
            return ""
            
        except:
            return ""
    
    def determine_input_value(self, question_text, input_element):
        """Determine appropriate value for a text input based on question"""
        question_lower = question_text.lower()
        
        try:
            # Years of experience questions
            if any(phrase in question_lower for phrase in ['years of experience', 'how many years', 'years of work']):
                # Check technology skills
                for tech, years in getattr(self, 'technology', {}).items():
                    if tech.lower() in question_lower:
                        return years
                
                # Check industry skills
                for industry, years in getattr(self, 'industry', {}).items():
                    if industry.lower() in question_lower:
                        return years
                
                # Default experience
                return getattr(self, 'technology', {}).get('default', 2)
            
            # Personal information
            personal_info = getattr(self, 'personal_info', {})
            if 'first name' in question_lower:
                return personal_info.get('First Name', '')
            elif 'last name' in question_lower:
                return personal_info.get('Last Name', '')  
            elif 'phone' in question_lower:
                return personal_info.get('Mobile Phone Number', '')
            elif 'email' in question_lower:
                return personal_info.get('Email', '')
            
            # GPA questions
            elif any(phrase in question_lower for phrase in ['gpa', 'grade point average']):
                return getattr(self, 'university_gpa', '3.5')
            
            # Salary questions (skip these)
            elif any(phrase in question_lower for phrase in ['salary', 'compensation', 'pay', 'wage']):
                return None
            
            # For numeric fields, provide a reasonable default
            input_type = input_element.get_attribute('type')
            if input_type in ['number', 'tel']:
                return 2  # Default years/numeric value
            
            # For text fields that seem to need a value
            elif input_type == 'text' and any(phrase in question_lower for phrase in ['city', 'location', 'address']):
                return personal_info.get('City', '')
            
            # Skip other text fields to avoid filling unwanted fields
            return None
            
        except:
            return None
    
    def determine_dropdown_value(self, question_text, select_obj):
        """Determine appropriate value for a dropdown based on question"""
        question_lower = question_text.lower()
        
        try:
            options = [opt.text for opt in select_obj.options]
            
            # Work authorization dropdowns
            if any(phrase in question_lower for phrase in ['work authorization', 'authorized to work', 'legally authorized']):
                for option in options:
                    if any(phrase in option.lower() for phrase in ['yes', 'authorized', 'eligible']):
                        return option
            
            # Visa sponsorship dropdowns  
            elif any(phrase in question_lower for phrase in ['visa', 'sponsorship', 'sponsor']):
                for option in options:
                    if any(phrase in option.lower() for phrase in ['no', 'not required', 'do not']):
                        return option
            
            # Experience level dropdowns
            elif 'experience' in question_lower and 'level' in question_lower:
                # Look for mid-level options
                for option in options:
                    if any(phrase in option.lower() for phrase in ['mid', '3-5', '2-4', 'intermediate']):
                        return option
                # Fallback to second option (avoid "Select" and go for entry level)
                if len(options) > 1:
                    return options[1]
            
            # Default: don't change dropdown
            return None
            
        except:
            return None
    
    def intelligent_radio_selection(self, radio_buttons, question_text, container):
        """Intelligent radio button selection with enhanced logic"""
        try:
            # Use the existing smart_radio_selection method
            return self.smart_radio_selection(radio_buttons, question_text.lower())
            
        except Exception as e:
            print(f"            ❌ Intelligent radio selection error: {str(e)}")
            return False
    
    def analyze_and_select_best_button(self, all_buttons):
        """Analyze all buttons and select the best next/continue button"""
        try:
            print(f"      📊 Analyzing {len(all_buttons)} buttons on the page...")
            
            button_candidates = []
            
            for i, btn in enumerate(all_buttons):
                try:
                    # Get button properties
                    aria_label = btn.get_attribute('aria-label') or ""
                    button_text = btn.text.strip().lower()
                    button_classes = btn.get_attribute('class') or ""
                    button_id = btn.get_attribute('id') or ""
                    data_attrs = {attr: btn.get_attribute(attr) for attr in ['data-easy-apply-next-button', 'data-live-test-easy-apply-next-button'] if btn.get_attribute(attr)}
                    
                    # Skip if button is not visible or not enabled
                    if not btn.is_displayed() or not btn.is_enabled():
                        continue
                    
                    # Calculate button score
                    score = 0
                    reasons = []
                    
                    # Highest priority: LinkedIn-specific attributes
                    if data_attrs:
                        score += 10
                        reasons.append("LinkedIn-specific data attribute")
                    
                    # High priority: Explicit next/continue/submit/review in aria-label
                    if any(keyword in aria_label.lower() for keyword in ['continue to next step', 'review your application', 'submit application']):
                        score += 8
                        reasons.append("Explicit next action in aria-label")
                    elif any(keyword in aria_label.lower() for keyword in ['continue', 'next', 'submit', 'review']):
                        score += 6
                        reasons.append("Action keyword in aria-label")
                    
                    # Medium priority: Action words in button text
                    if any(keyword in button_text for keyword in ['continue', 'next', 'submit', 'review']):
                        score += 4
                        reasons.append("Action keyword in button text")
                    
                    # Medium priority: Primary button styling
                    if 'artdeco-button--primary' in button_classes:
                        score += 3
                        reasons.append("Primary button styling")
                    
                    # Penalty: Back buttons (should be avoided)
                    if any(keyword in aria_label.lower() or keyword in button_text for keyword in ['back', 'previous']):
                        score -= 5
                        reasons.append("PENALTY: Back/Previous button")
                    
                    # Bonus: Position-based (later buttons in DOM usually progress forward)
                    if i > len(all_buttons) / 2:
                        score += 1
                        reasons.append("Later in DOM order")
                    
                    if score > 0:  # Only consider buttons with positive scores
                        button_candidates.append({
                            'button': btn,
                            'score': score,
                            'text': button_text,
                            'aria_label': aria_label,
                            'reasons': reasons,
                            'index': i
                        })
                        
                        print(f"      Button {i+1}: '{button_text}' | aria: '{aria_label}' | score: {score} | reasons: {', '.join(reasons)}")
                
                except Exception as btn_error:
                    continue
            
            # Select the best candidate
            if button_candidates:
                # Sort by score, highest first
                button_candidates.sort(key=lambda x: x['score'], reverse=True)
                best_button = button_candidates[0]
                
                print(f"      ✅ Selected best button: '{best_button['text']}' (score: {best_button['score']})")
                print(f"         Reasons: {', '.join(best_button['reasons'])}")
                
                return best_button['button']
            else:
                print("      ❌ No suitable buttons found after analysis")
                return None
                
        except Exception as e:
            print(f"      ❌ Error in button analysis: {str(e)}")
            return None
    
    def ensure_optimal_viewport(self):
        """Ensure browser viewport is optimized for form visibility"""
        try:
            # Get current window size
            current_size = self.browser.get_window_size()
            print(f"      📱 Current window size: {current_size['width']}x{current_size['height']}")
            
            # Ensure minimum size for form visibility
            if current_size['width'] < 1920 or current_size['height'] < 1080:
                print("      📱 Adjusting window size for better form visibility...")
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_window()
            
            # Ensure zoom level is set for maximum form visibility
            current_zoom = self.browser.execute_script("return document.body.style.zoom || '1'")
            if current_zoom != '0.8':
                print("      🔍 Setting zoom level to 80% for better element visibility...")
                self.browser.execute_script("document.body.style.zoom='0.8'")
            
            # Scroll to top to ensure form elements are visible
            self.browser.execute_script("window.scrollTo(0, 0);")
            
        except Exception as e:
            print(f"      ⚠️  Could not optimize viewport: {str(e)}")
    
    def print_ai_stats(self):
        """Print AI application statistics"""
        total_ai_attempts = self.ai_success_count + self.ai_failure_count
        if total_ai_attempts > 0:
            success_rate = (self.ai_success_count / total_ai_attempts) * 100
            print(f"\n🤖 AI Application Statistics:")
            print(f"   Total AI attempts: {total_ai_attempts}")
            print(f"   Successful: {self.ai_success_count}")
            print(f"   Failed: {self.ai_failure_count}")
            print(f"   Success rate: {success_rate:.1f}%")
        else:
            print("\n🤖 No AI applications attempted")
    
    async def cleanup(self):
        """Clean up browser-use resources"""
        if self.browser_use_bot:
            try:
                await self.browser_use_bot.close()
                logger.info("Browser-use resources cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up browser-use: {str(e)}")


# Configuration helper for enhanced bot
def create_enhanced_config(original_config):
    """Add AI-specific configuration options"""
    enhanced_config = original_config.copy()
    
    # Add AI form handling option (default: True)
    enhanced_config['useAIForms'] = enhanced_config.get('useAIForms', True)
    
    # Add AI confidence threshold (how confident AI should be before proceeding)
    enhanced_config['aiConfidenceThreshold'] = enhanced_config.get('aiConfidenceThreshold', 0.8)
    
    # Add AI retry attempts
    enhanced_config['aiRetryAttempts'] = enhanced_config.get('aiRetryAttempts', 2)
    
    return enhanced_config


# Example usage function
def run_enhanced_bot():
    """Example of how to run the enhanced LinkedIn bot"""
    
    print("🚀 Starting Enhanced LinkedIn Easy Apply Bot with AI")
    
    # Your existing configuration loading logic here
    # This is just an example - replace with your actual config loading
    
    import yaml
    
    # Load configuration
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Enhance config with AI options
    enhanced_config = create_enhanced_config(config)
    
    # Initialize your webdriver (your existing logic)
    # driver = initialize_driver()  # Your driver initialization
    
    # Create enhanced bot instance
    # bot = EnhancedLinkedInEasyApply(enhanced_config, driver)
    
    print("✅ Enhanced bot configured successfully")
    print(f"🤖 AI form handling: {'Enabled' if enhanced_config.get('useAIForms', True) else 'Disabled'}")
    
    # Your existing bot running logic here
    # bot.start_applying()
    
    # Print AI statistics when done
    # bot.print_ai_stats()
    
    # Clean up
    # asyncio.run(bot.cleanup())


if __name__ == "__main__":
    run_enhanced_bot()