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
from selenium.webdriver.common.action_chains import ActionChains
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
        
        # Initialize browser-use components (AI-only mode)
        self.use_ai_forms = parameters.get('useAIForms', True)  # AI enabled
        self.form_handling_mode = parameters.get('formHandlingMode', 'ai-only')  # AI-only mode
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
                # Always use thread-based execution for better compatibility
                print("      🔄 Using thread-based async execution for better compatibility...")
                
                def run_in_new_loop():
                    # Create completely new event loop in this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(_async_apply())
                    finally:
                        new_loop.close()
                
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    try:
                        return future.result(timeout=180)  # 3 minute total timeout
                    except concurrent.futures.TimeoutError:
                        print("      ❌ Thread execution timed out")
                        return False
                    
            except Exception as execution_error:
                print(f"      ❌ Critical async execution error: {str(execution_error)}")
                self.ai_failure_count += 1
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

        # Determine form handling approach based on mode
        print(f"🔧 Form handling mode: {self.form_handling_mode}")
        print(f"🤖 AI available: {'✅ Yes' if (self.use_ai_forms and self.openai_api_key) else '❌ No'}")
        
        if self.form_handling_mode == 'hardcoded-only':
            print("🔧 Using hardcoded-only form handling...")
            return self._manual_apply_to_job(job_title, company, debug_folder)
        
        elif self.form_handling_mode == 'ai-only':
            print("🤖 Using AI-only form handling...")
            if not self.use_ai_forms or not self.openai_api_key:
                print("❌ AI-only mode requested but AI is not available")
                print(f"   - use_ai_forms: {self.use_ai_forms}")
                print(f"   - openai_api_key: {'Present' if self.openai_api_key else 'Missing'}")
                raise Exception("AI-only mode requested but AI is not configured properly")
            
            print("🎯 Starting AI-only application process...")
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
        
        print(f"🔧 Beginning form processing loop (max steps: {self.max_form_steps})")
        
        while submit_application_text not in button_text.lower() and form_step_count < self.max_form_steps:
            form_step_count += 1
            print(f"📝 Processing form step {form_step_count}/{self.max_form_steps}")
            print(f"   📊 Current URL: {self.browser.current_url}")
            
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
                    
                    # Store current page state to detect changes
                    current_url = self.browser.current_url
                    current_page_hash = hash(self.browser.page_source[:1000])  # First 1000 chars as fingerprint
                    
                    # Use enhanced button finding logic
                    print("   🔍 Looking for next/submit button...")
                    next_button = self.find_next_button_advanced()
                    
                    if not next_button:
                        # Fallback to original selectors
                        print("   🔄 Fallback: Using original button selectors...")
                        next_button_selectors = [
                            (By.CLASS_NAME, "artdeco-button--primary"),
                            (By.CSS_SELECTOR, "button[aria-label*='Continue']"),
                            (By.CSS_SELECTOR, "button[aria-label*='Review']"),
                            (By.CSS_SELECTOR, "button[aria-label*='Submit']"),
                            (By.CSS_SELECTOR, "button.artdeco-button--primary")
                        ]
                        next_button = self.smart_find_element(next_button_selectors, timeout=10)
                    
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
                    
                    # Special handling for Review button
                    if 'review' in button_text or 'review' in button_aria.lower():
                        print("   📋 This is the Review button - proceeding to application review")
                    elif submit_application_text in button_text:
                        print("   🎯 This is the final submit button!")
                        try:
                            print("   📤 Attempting to unfollow company before submission...")
                            self.unfollow()
                            print("   ✅ Unfollowed company successfully")
                        except Exception as e:
                            print(f"   ⚠️  Failed to unfollow company: {str(e)}")
                    
                    print(f"   ⏱️  Waiting {1 * self.sleep_multiplier}-{1.5 * self.sleep_multiplier}s before clicking...")
                    time.sleep(random.uniform(1, 1.5) * self.sleep_multiplier)
                    
                    # Ensure button is visible and scrolled into view before clicking
                    print("   📍 Ensuring button is visible before clicking...")
                    self.scroll_to_element(next_button)
                    
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
                        
                        # Enhanced page change detection
                        print("   📊 Checking page state changes after button click...")
                        new_url = self.browser.current_url
                        new_page_hash = hash(self.browser.page_source[:1000])
                        
                        print(f"      URL changed: {current_url != new_url}")
                        print(f"      Page content changed: {current_page_hash != new_page_hash}")
                        print(f"      New URL: {new_url}")
                        print(f"      New page title: {self.browser.title}")
                        
                        # If neither URL nor content changed, this might indicate the button click didn't work
                        if current_url == new_url and current_page_hash == new_page_hash:
                            print("   ⚠️  WARNING: Page appears unchanged after button click!")
                            print("   📊 This might indicate a stuck state or validation errors")
                            
                            # Special handling for Review button - it might just change content without URL change
                            if 'review' in button_text or 'review' in button_aria.lower():
                                print("   📋 Review button clicked - checking for review page content changes...")
                                
                                # Look for review page indicators
                                review_indicators = [
                                    "review your application",
                                    "application review",
                                    "submit application",
                                    "final review",
                                    "confirm",
                                    "ready to submit"
                                ]
                                
                                page_content_lower = self.browser.page_source.lower()
                                review_content_found = any(indicator in page_content_lower for indicator in review_indicators)
                                
                                if review_content_found:
                                    print("   ✅ Review page content detected - button click was successful")
                                else:
                                    print("   ⚠️  Review page content not found - trying alternative detection")
                                    # Try to find validation errors more aggressively
                                    self.detect_stuck_form_state()
                            else:
                                # Try to find validation errors more aggressively
                                self.detect_stuck_form_state()
                                
                            # Check if we're specifically stuck at Review button
                            if self.is_stuck_at_review_button():
                                print("   🔄 Detected stuck at Review button - attempting advanced fix")
                                self.fix_review_button_issue()

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
    
    def find_next_button_advanced(self):
        """Advanced button finding with specific priority for LinkedIn patterns"""
        try:
            print("      🎯 Using advanced button detection logic...")
            
            # First, scroll to ensure all buttons are visible
            print("      📜 Scrolling to reveal buttons that might be below the fold...")
            self.scroll_to_reveal_buttons()
            
            # Method 1: Look for buttons with specific LinkedIn data attributes
            linkedin_buttons = self.browser.find_elements(By.CSS_SELECTOR, 
                "button[data-easy-apply-next-button], button[data-live-test-easy-apply-next-button], button[data-live-test-easy-apply-review-button]")
            
            if linkedin_buttons:
                for btn in linkedin_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        btn_text = btn.text.strip().lower()
                        btn_aria = (btn.get_attribute('aria-label') or '').lower()
                        print(f"      ✅ Found LinkedIn-specific button: '{btn_text}' / '{btn_aria}'")
                        # Ensure button is in view before returning
                        self.scroll_to_element(btn)
                        return btn
            
            # Method 2: Look for primary buttons in the button container div
            button_containers = self.browser.find_elements(By.CSS_SELECTOR, 
                "div.display-flex.justify-flex-end, div[class*='button-container'], div[class*='form-actions']")
            
            for container in button_containers:
                primary_buttons = container.find_elements(By.CSS_SELECTOR, 
                    "button.artdeco-button--primary")
                
                for btn in primary_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        btn_text = btn.text.lower().strip()
                        btn_aria = (btn.get_attribute('aria-label') or '').lower()
                        
                        # Prioritize based on text/aria-label content
                        if any(keyword in btn_text + ' ' + btn_aria for keyword in ['next', 'continue', 'review', 'submit']):
                            print(f"      ✅ Found primary button in container: '{btn_text}' / '{btn_aria}'")
                            # Ensure button is in view before returning
                            self.scroll_to_element(btn)
                            return btn
            
            # Method 3: Look for buttons by aria-label with exact matching
            aria_selectors = [
                "button[aria-label='Continue to next step']",
                "button[aria-label='Review your application']", 
                "button[aria-label='Submit application']",
                "button[aria-label*='Continue']",
                "button[aria-label*='Next']",
                "button[aria-label*='Review']"
            ]
            
            for selector in aria_selectors:
                try:
                    buttons = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            print(f"      ✅ Found button by aria-label: {btn.get_attribute('aria-label')}")
                            # Ensure button is in view before returning
                            self.scroll_to_element(btn)
                            return btn
                except:
                    continue
            
            # Method 4: Last resort - look for any primary button that's not "Back"
            primary_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
            for btn in primary_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    btn_text = btn.text.lower().strip()
                    btn_aria = (btn.get_attribute('aria-label') or '').lower()
                    
                    # Exclude back buttons
                    if 'back' not in btn_text and 'back' not in btn_aria and 'previous' not in btn_aria:
                        print(f"      ⚠️  Found fallback primary button: '{btn_text}' / '{btn_aria}'")
                        # Ensure button is in view before returning
                        self.scroll_to_element(btn)
                        return btn
            
            print("      ❌ No suitable next button found with advanced detection")
            return None
            
        except Exception as e:
            print(f"      ❌ Error in advanced button detection: {str(e)}")
            return None
    
    def detect_stuck_form_state(self):
        """Detect why the form might be stuck and attempt to resolve"""
        try:
            print("      🔍 Analyzing stuck form state...")
            
            # Check for validation errors that weren't caught earlier
            error_indicators = [
                'please make a selection',
                'please enter a valid',
                'this field is required',
                'please complete this required field',
                'invalid format',
                'field cannot be empty'
            ]
            
            page_source_lower = self.browser.page_source.lower()
            found_errors = []
            
            for error in error_indicators:
                if error in page_source_lower:
                    count = page_source_lower.count(error)
                    found_errors.append(f"{error} ({count} times)")
            
            if found_errors:
                print(f"      ⚠️  Found potential validation errors:")
                for error in found_errors[:5]:  # Show first 5
                    print(f"         - {error}")
                
                # Try to fix these issues
                print("      🔧 Attempting to resolve validation errors...")
                self.emergency_form_fix()
            else:
                print("      ✅ No obvious validation errors found")
                
            # Check if the button is actually clickable
            try:
                next_buttons = self.browser.find_elements(By.CSS_SELECTOR, 
                    "button.artdeco-button--primary, button[aria-label*='Continue'], button[aria-label*='Next']")
                
                print(f"      📊 Found {len(next_buttons)} potential next buttons:")
                for i, btn in enumerate(next_buttons):
                    try:
                        is_displayed = btn.is_displayed()
                        is_enabled = btn.is_enabled()
                        btn_text = btn.text.strip()
                        btn_aria = btn.get_attribute('aria-label') or ''
                        
                        print(f"         Button {i+1}: '{btn_text}' / '{btn_aria}' - Displayed: {is_displayed}, Enabled: {is_enabled}")
                        
                        if not is_enabled:
                            print(f"         ⚠️  Button {i+1} is disabled - this might be the issue!")
                            
                    except Exception as btn_error:
                        print(f"         Button {i+1}: Error analyzing - {str(btn_error)}")
                        
            except Exception as analysis_error:
                print(f"      ❌ Error analyzing buttons: {str(analysis_error)}")
                
        except Exception as e:
            print(f"      ❌ Error in stuck state detection: {str(e)}")
    
    def emergency_form_fix(self):
        """Emergency form fixing when stuck"""
        try:
            print("         🚨 Running emergency form fixes...")
            
            # Fix 1: Try to select any unselected radio buttons
            radio_groups = self.browser.find_elements(By.CSS_SELECTOR, "fieldset, div[role='radiogroup']")
            fixed_radios = 0
            
            for group in radio_groups:
                try:
                    radios = group.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radios:
                        selected = [r for r in radios if r.is_selected()]
                        if not selected:
                            # Select the first radio button
                            radios[0].click()
                            fixed_radios += 1
                            print(f"         ✅ Fixed unselected radio group ({fixed_radios})")
                except:
                    continue
            
            # Fix 2: Fill any empty required text fields with minimal values
            required_inputs = self.browser.find_elements(By.CSS_SELECTOR, "input[required], input[aria-required='true']")
            fixed_inputs = 0
            
            for input_elem in required_inputs:
                try:
                    if input_elem.get_attribute('type') in ['text', 'number', 'tel', 'email']:
                        current_value = input_elem.get_attribute('value') or ''
                        if not current_value.strip():
                            input_type = input_elem.get_attribute('type')
                            if input_type == 'number':
                                input_elem.send_keys('1')
                            elif input_type == 'email':
                                input_elem.send_keys('email@example.com')
                            else:
                                input_elem.send_keys('N/A')
                            fixed_inputs += 1
                            print(f"         ✅ Fixed empty required field ({fixed_inputs})")
                except:
                    continue
            
            print(f"         📊 Emergency fixes applied: {fixed_radios} radio groups, {fixed_inputs} text fields")
            
        except Exception as e:
            print(f"         ❌ Error in emergency form fix: {str(e)}")
    
    def handle_linkedin_radio_buttons(self):
        """Handle specific LinkedIn radio button structure from the provided HTML"""
        try:
            print("         📋 Handling LinkedIn-specific radio button structures...")
            
            # Find all fieldsets with the LinkedIn radio button component
            fieldsets = self.browser.find_elements(By.CSS_SELECTOR, 'fieldset[data-test-form-builder-radio-button-form-component]')
            
            fixed_count = 0
            for fieldset in fieldsets:
                try:
                    # Get the legend text to understand the question
                    legend = fieldset.find_element(By.TAG_NAME, 'legend')
                    question_text = legend.text.strip().lower()
                    
                    print(f"         🎯 Processing LinkedIn radio question: '{question_text[:60]}...'")
                    
                    # Check if any radio button in this fieldset is already selected
                    radio_buttons = fieldset.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
                    selected_radios = [r for r in radio_buttons if r.is_selected()]
                    
                    if len(selected_radios) == 0 and len(radio_buttons) > 0:
                        print(f"         ⚠️  No selection made - need to select appropriate option")
                        
                        # Get all the radio options and their labels
                        options = []
                        for radio in radio_buttons:
                            try:
                                radio_id = radio.get_attribute('id')
                                label = self.browser.find_element(By.CSS_SELECTOR, f'label[for="{radio_id}"]')
                                option_text = label.text.strip().lower()
                                options.append((radio, option_text))
                                print(f"            Option: '{option_text}'")
                            except:
                                continue
                        
                        # Smart selection based on question type
                        selected = False
                        
                        # Work authorization questions
                        if any(keyword in question_text for keyword in ['authorized', 'legally', 'work in', 'without restriction']):
                            print("         🔐 Detected work authorization question - selecting 'Yes'")
                            for radio, option_text in options:
                                if 'yes' in option_text:
                                    try:
                                        radio.click()
                                        selected = True
                                        fixed_count += 1
                                        print(f"         ✅ Selected: '{option_text}'")
                                        break
                                    except Exception as click_error:
                                        print(f"         ❌ Could not click option: {str(click_error)}")
                        
                        # Visa sponsorship questions
                        elif any(keyword in question_text for keyword in ['visa', 'sponsor', 'sponsorship', 'transfer']):
                            print("         🛂 Detected visa sponsorship question - selecting 'No'")
                            for radio, option_text in options:
                                if 'no' in option_text:
                                    try:
                                        radio.click()
                                        selected = True
                                        fixed_count += 1
                                        print(f"         ✅ Selected: '{option_text}'")
                                        break
                                    except Exception as click_error:
                                        print(f"         ❌ Could not click option: {str(click_error)}")
                        
                        # Default to first option if no specific match
                        if not selected and options:
                            print("         🔄 No specific match - selecting first available option")
                            try:
                                options[0][0].click()
                                fixed_count += 1
                                print(f"         ✅ Selected default: '{options[0][1]}'")
                            except Exception as click_error:
                                print(f"         ❌ Could not click default option: {str(click_error)}")
                    else:
                        print(f"         ✅ Radio group already has selection ({len(selected_radios)} selected)")
                        
                except Exception as fieldset_error:
                    print(f"         ❌ Error processing fieldset: {str(fieldset_error)}")
                    continue
            
            print(f"         ✅ LinkedIn radio buttons processed: {fixed_count} groups fixed")
            
        except Exception as e:
            print(f"         ❌ Error in LinkedIn radio button handling: {str(e)}")
    
    def is_stuck_at_review_button(self):
        """Check if we're stuck at the Review button based on specific patterns"""
        try:
            # Look for the exact HTML pattern from the user's example
            review_button_container = self.browser.find_elements(By.CSS_SELECTOR, "div.display-flex.justify-flex-end")
            
            for container in review_button_container:
                try:
                    # Look for both Back and Review buttons in the same container
                    back_button = container.find_elements(By.CSS_SELECTOR, "button[aria-label*='Back']")
                    review_button = container.find_elements(By.CSS_SELECTOR, "button[aria-label*='Review']")
                    
                    if back_button and review_button:
                        # Check if the Review button has the specific attributes
                        for review_btn in review_button:
                            if (review_btn.get_attribute('data-live-test-easy-apply-review-button') is not None or
                                'review' in review_btn.text.lower()):
                                print("         🎯 Found Review button stuck pattern")
                                return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            print(f"         ❌ Error checking Review button stuck state: {str(e)}")
            return False
    
    def fix_review_button_issue(self):
        """Attempt to fix issues with Review button not advancing"""
        try:
            print("         🔧 Applying Review button specific fixes...")
            
            # Method 1: Force scroll to Review button and retry
            review_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button[aria-label*='Review']")
            
            for review_btn in review_buttons:
                if review_btn.is_displayed() and review_btn.is_enabled():
                    try:
                        print("         📍 Scrolling to Review button...")
                        self.browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", review_btn)
                        time.sleep(1)
                        
                        print("         🖱️  Attempting enhanced Review button click...")
                        
                        # Try multiple click methods
                        click_success = False
                        
                        # Method 1: Regular click
                        try:
                            review_btn.click()
                            click_success = True
                            print("         ✅ Review button clicked with regular click")
                        except:
                            pass
                        
                        # Method 2: JavaScript click
                        if not click_success:
                            try:
                                self.browser.execute_script("arguments[0].click();", review_btn)
                                click_success = True
                                print("         ✅ Review button clicked with JavaScript")
                            except:
                                pass
                        
                        # Method 3: Mouse action
                        if not click_success:
                            try:
                                from selenium.webdriver.common.action_chains import ActionChains
                                actions = ActionChains(self.browser)
                                actions.move_to_element(review_btn).click().perform()
                                click_success = True
                                print("         ✅ Review button clicked with ActionChains")
                            except:
                                pass
                        
                        if click_success:
                            # Wait longer for Review page to load
                            print("         ⏳ Waiting for Review page to load...")
                            time.sleep(3)
                            
                            # Check if we advanced to review page
                            page_source = self.browser.page_source.lower()
                            if any(indicator in page_source for indicator in ['submit application', 'final review', 'ready to submit']):
                                print("         ✅ Successfully advanced to Review page")
                                return True
                            else:
                                print("         ⚠️  Review button clicked but page didn't advance")
                        
                    except Exception as btn_error:
                        print(f"         ❌ Error clicking Review button: {str(btn_error)}")
                        continue
            
            # Method 2: Check for form validation issues preventing Review
            print("         🔍 Checking for validation issues preventing Review...")
            
            # Look for any validation errors on the current page
            validation_errors = self.browser.find_elements(By.CSS_SELECTOR, 
                ".artdeco-inline-feedback--error, .error, [class*='error']")
            
            if validation_errors:
                print(f"         ⚠️  Found {len(validation_errors)} validation errors")
                for i, error in enumerate(validation_errors[:3]):  # Show first 3
                    try:
                        error_text = error.text.strip()
                        if error_text:
                            print(f"            Error {i+1}: {error_text}")
                    except:
                        print(f"            Error {i+1}: Could not read error text")
                
                # Try to fix validation errors
                print("         🚨 Running emergency validation fixes...")
                self.emergency_form_fix()
                
            return False
            
        except Exception as e:
            print(f"         ❌ Error in Review button fix: {str(e)}")
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
            
            # Handle LinkedIn-specific radio buttons first
            self.handle_linkedin_radio_buttons()
            
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
            
            # Method 2: New LinkedIn fieldset structure (specific to your HTML)
            containers_fieldset = self.browser.find_elements(By.CSS_SELECTOR, 'fieldset[data-test-form-builder-radio-button-form-component]')
            all_containers.extend(containers_fieldset)
            
            # Method 3: New artdeco structure
            containers_new = self.browser.find_elements(By.CSS_SELECTOR, '.artdeco-card, fieldset, [data-test-form-element]')
            all_containers.extend(containers_new)
            
            # Method 4: Generic form containers
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
    
    def scroll_to_reveal_buttons(self):
        """Scroll page to reveal buttons that might be below the fold"""
        try:
            print("         📜 Performing systematic scroll to reveal all buttons...")
            
            # Method 1: Scroll to bottom of the page to reveal any hidden buttons
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # Method 2: Scroll to find button containers
            button_container_selectors = [
                "div.display-flex.justify-flex-end",
                "div[class*='button-container']",
                "div[class*='form-actions']",
                ".jobs-easy-apply-modal__footer",
                ".artdeco-modal__actionbar"
            ]
            
            for selector in button_container_selectors:
                try:
                    containers = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    for container in containers:
                        if container.is_displayed():
                            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
                            time.sleep(0.3)
                            print(f"         📍 Scrolled to button container: {selector}")
                            break
                except:
                    continue
            
            # Method 3: Smart scroll to find any primary buttons
            try:
                primary_buttons = self.browser.find_elements(By.CSS_SELECTOR, "button.artdeco-button--primary")
                for btn in primary_buttons[-3:]:  # Check last 3 primary buttons (likely to be submit/next)
                    try:
                        btn_text = btn.text.strip().lower()
                        if any(keyword in btn_text for keyword in ['next', 'continue', 'review', 'submit']):
                            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.3)
                            print(f"         📍 Scrolled to primary button: '{btn_text}'")
                            break
                    except:
                        continue
            except:
                pass
            
            # Method 4: Ensure we can see both top and bottom of form
            print("         📜 Final scroll adjustments...")
            # Scroll up a bit to make sure we can see the full button area
            self.browser.execute_script("window.scrollBy(0, -100);")
            time.sleep(0.3)
            
            print("         ✅ Scroll to reveal buttons completed")
            
        except Exception as e:
            print(f"         ❌ Error during scroll to reveal buttons: {str(e)}")
    
    def scroll_to_element(self, element):
        """Scroll to specific element to ensure it's visible and clickable"""
        try:
            print(f"         📍 Scrolling to element to ensure visibility...")
            
            # Method 1: Standard scroll into view
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)
            
            # Method 2: Ensure element is not obscured by checking its position
            element_rect = element.rect
            window_height = self.browser.execute_script("return window.innerHeight;")
            
            # If element is too close to bottom, scroll up a bit more
            if element_rect['y'] > window_height * 0.8:
                self.browser.execute_script("window.scrollBy(0, -150);")
                time.sleep(0.3)
            
            # If element is too close to top, scroll down a bit
            elif element_rect['y'] < window_height * 0.1:
                self.browser.execute_script("window.scrollBy(0, 150);")
                time.sleep(0.3)
            
            print(f"         ✅ Element scrolled into optimal view position")
            
        except Exception as e:
            print(f"         ⚠️  Warning: Could not scroll to element: {str(e)}")
    
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