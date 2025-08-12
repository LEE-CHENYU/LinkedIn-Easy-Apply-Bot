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
        
        async def _async_apply():
            """Async wrapper for AI application"""
            try:
                # Initialize AI agent if not already done
                if not self.browser_use_bot:
                    success = await self.initialize_ai_agent()
                    if not success:
                        return False
                
                # Use AI to handle the application
                logger.info(f"Using AI to apply for {job_title} at {company}")
                
                success = await self.browser_use_bot.handle_application_popup(
                    job_title, company
                )
                
                if success:
                    self.ai_success_count += 1
                    logger.info(f"✅ AI successfully applied to {job_title} at {company}")
                else:
                    self.ai_failure_count += 1
                    logger.warning(f"❌ AI failed to apply to {job_title} at {company}")
                
                return success
                
            except Exception as e:
                self.ai_failure_count += 1
                logger.error(f"AI application error: {str(e)}")
                return False
        
        # Run the async function
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_async_apply())
    
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

        # Try AI-powered form handling first
        if self.use_ai_forms:
            try:
                print("🤖 Attempting AI-powered application...")
                print(f"   - Job: {job_title}")
                print(f"   - Company: {company}")
                print(f"   - Using OpenAI API key: {'✅ Available' if self.openai_api_key else '❌ Missing'}")
                
                ai_success = self.apply_to_job_with_ai(job_title, company)
                
                if ai_success:
                    print(f"✅ AI successfully completed application for {job_title}")
                    return True
                else:
                    print("❌ AI application failed, falling back to manual method...")
                    print("   - This may be due to complex forms or AI limitations")
                    
            except Exception as e:
                print(f"❌ AI application error: {str(e)}")
                print("   - Falling back to manual method...")
                import traceback
                print(f"   - Error details: {traceback.format_exc()}")
        else:
            print("🤖 AI form handling is disabled, using manual method")
        
        # Fallback to original manual method
        print("🔧 Using manual form handling...")
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
                    
                    # Call fill_up() with detailed logging
                    print("   📝 Calling fill_up() method...")
                    self.fill_up()
                    print("   ✅ fill_up() completed")
                    
                    # Use smart element finder for next button
                    print("   🔍 Looking for next/submit button...")
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
                                for i, error_elem in enumerate(error_elements):
                                    try:
                                        # Find the parent fieldset or form group
                                        parent = error_elem.find_element(By.XPATH, "./ancestor::fieldset | ./ancestor::div[contains(@class, 'form-group')]")
                                        question_text = parent.find_element(By.CSS_SELECTOR, "legend, label, .fb-form-element-label").text
                                        print(f"      Error {i+1}: '{question_text}'")
                                    except:
                                        print(f"      Error {i+1}: Could not determine question text")
                            except:
                                print("      Could not analyze specific radio button errors")
                        
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