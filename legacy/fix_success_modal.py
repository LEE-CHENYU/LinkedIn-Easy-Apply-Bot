#!/usr/bin/env python3
"""
Fix for handling LinkedIn success modal after application submission
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def handle_success_modal(page: Page) -> bool:
    """
    Handle the LinkedIn success modal that appears after application submission
    
    Args:
        page: Playwright page object
        
    Returns:
        bool: True if modal was handled successfully
    """
    try:
        # Check for success indicators
        success_selectors = [
            "text='Your application was sent'",
            "text='Application sent'",
            "text='Thank you for applying'",
            "text='Application submitted'",
            "[aria-label='Dismiss']",
            "button:has-text('Done')",
            "button:has-text('Close')",
            "[data-test-modal-close-btn]"
        ]
        
        # Wait for success modal to appear
        for selector in success_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=3000)
                if element:
                    logger.info(f"✅ Found success indicator: {selector}")
                    
                    # Try to find and click dismiss/done button
                    dismiss_buttons = [
                        "[aria-label='Dismiss']",
                        "button:has-text('Done')",
                        "button:has-text('Close')",
                        "[data-test-modal-close-btn]",
                        ".artdeco-modal__dismiss",
                        "[aria-label*='Dismiss']",
                        "[aria-label*='Close']"
                    ]
                    
                    for button_selector in dismiss_buttons:
                        try:
                            button = await page.query_selector(button_selector)
                            if button and await button.is_visible():
                                logger.info(f"🔄 Clicking dismiss button: {button_selector}")
                                await button.click()
                                await asyncio.sleep(2)
                                return True
                        except:
                            continue
                    
                    # If no dismiss button found, try pressing Escape
                    logger.info("⌨️ Pressing Escape to close modal")
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(2)
                    return True
                    
            except:
                continue
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error handling success modal: {str(e)}")
        return False


async def enhanced_apply_with_ai(self, job_title: str, company: str) -> bool:
    """
    Enhanced version of apply_with_ai that handles success modals
    
    This is a patch that should be integrated into the main bot
    """
    try:
        # Original application logic
        result = await self.original_apply_with_ai(job_title, company)
        
        if result:
            logger.info("✅ Application submitted, checking for success modal...")
            
            # Handle success modal
            modal_handled = await handle_success_modal(self.page)
            
            if modal_handled:
                logger.info("✅ Success modal dismissed, ready for next job")
            else:
                logger.warning("⚠️ No success modal found or couldn't dismiss it")
                
                # Try alternative dismissal methods
                try:
                    # Click outside modal
                    await self.page.click("body", position={"x": 10, "y": 10})
                    await asyncio.sleep(1)
                except:
                    pass
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced apply: {str(e)}")
        return False


# Patch for the Playwright bot
def patch_playwright_bot():
    """
    Apply the success modal handling patch to the Playwright bot
    
    Add this to playwright_linkedin_bot.py after the apply_with_ai method
    """
    
    code_to_add = '''
    async def handle_application_success(self) -> bool:
        """Handle success modal after application submission"""
        try:
            # Check if we're on a success page
            page_content = await self.page.content()
            
            if any(indicator in page_content.lower() for indicator in 
                   ["your application was sent", "application sent", "thank you"]):
                
                logger.info("✅ Application success detected, handling modal...")
                
                # Try to close modal
                dismiss_selectors = [
                    "[aria-label='Dismiss']",
                    "button:has-text('Done')",
                    "[data-test-modal-close-btn]",
                    ".artdeco-modal__dismiss"
                ]
                
                for selector in dismiss_selectors:
                    try:
                        button = await self.page.query_selector(selector)
                        if button and await button.is_visible():
                            await button.click()
                            logger.info(f"✅ Dismissed success modal")
                            await asyncio.sleep(2)
                            return True
                    except:
                        continue
                
                # Fallback: Press Escape
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(1)
                
            return True
            
        except Exception as e:
            logger.error(f"Error handling success: {str(e)}")
            return False
    '''
    
    return code_to_add


if __name__ == "__main__":
    print("Success Modal Handler Fix")
    print("=" * 50)
    print("\nThis fix handles the LinkedIn success modal that appears after application submission.")
    print("\nTo apply this fix, add the following to your apply_with_ai method in playwright_linkedin_bot.py:")
    print("\n" + patch_playwright_bot())
    print("\nThen call handle_application_success() after a successful application.")