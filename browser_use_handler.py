#!/usr/bin/env python3
"""
Browser-use integration for LinkedIn Easy Apply Bot
Handles intelligent form filling using AI-powered browser automation
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from browser_use import Agent
from playwright.async_api import Page

class LinkedInFormHandler:
    """AI-powered LinkedIn application form handler using browser-use"""
    
    def __init__(self, config: Dict[str, Any], openai_api_key: str):
        """
        Initialize the LinkedIn form handler
        
        Args:
            config: Configuration dictionary with user preferences
            openai_api_key: OpenAI API key for AI agent
        """
        self.config = config
        self.api_key = openai_api_key
        self.agent = None
        self.logger = logging.getLogger(__name__)
        
        # Extract relevant config for form filling
        self.personal_info = config.get('personalInfo', {})
        self.checkboxes = config.get('checkboxes', {})
        self.technology = config.get('technology', {})
        self.industry = config.get('industry', {})
        self.university_gpa = config.get('universityGpa', '3.7')
        self.languages = config.get('languages', {})
        
    async def initialize_agent(self, page: Page):
        """Initialize the browser-use agent with the existing page"""
        try:
            from browser_use.llm import ChatOpenAI
            
            # Create LLM instance for OpenAI
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.api_key
            )
            
            # Create agent with task and LLM
            self.agent = Agent(
                task="Help fill out LinkedIn job application forms",
                llm=llm,
                page=page,         # Pass page directly
                use_vision=True,   # Enable vision for understanding form layouts
                save_conversation_path="./logs/browser_use_conversations"
            )
            
            self.logger.info("Browser-use agent initialized successfully with OpenAI GPT-4o")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser-use agent: {str(e)}")
            raise
    
    def _build_form_instructions(self) -> str:
        """Build comprehensive instructions for the AI agent"""
        
        instructions = f"""
You are helping fill out a LinkedIn job application form. Please follow these guidelines:

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
Technology Skills: {dict(list(self.technology.items())[:5])}  # Show first 5 items
Industry Experience: {dict(list(self.industry.items())[:5])}  # Show first 5 items
Default experience for unlisted skills: {self.technology.get('default', 1)} years

LANGUAGES:
{self.languages}

IMPORTANT RULES:
1. For "years of experience" questions, match the technology/skill mentioned in the question to the values above
2. For yes/no questions, use the work authorization values above
3. For dropdown selections, choose the most appropriate option based on the context
4. For text fields without specific matches, use reasonable defaults or leave professionally formatted spaces
5. For file uploads, skip them (they should be handled separately)
6. For EEO questions (gender, race, veteran status), select "Prefer not to answer" or "Decline to answer" if available
7. Always click "Continue" or "Next" buttons to proceed through the form
8. If you encounter "Submit Application", only click it if all required fields are properly filled

Please fill out this LinkedIn job application form step by step, following these instructions carefully.
"""
        
        return instructions.strip()
    
    async def handle_application_form(self, page: Page, job_title: str = "", company: str = "") -> bool:
        """
        Handle a LinkedIn application form using AI
        
        Args:
            page: Playwright page object
            job_title: Job title for context
            company: Company name for context
            
        Returns:
            bool: True if application was completed successfully
        """
        try:
            if not self.agent:
                await self.initialize_agent(page)
            
            # Build context-aware instructions
            context = f"Applying for {job_title} at {company}. " if job_title and company else ""
            instructions = context + self._build_form_instructions()
            
            self.logger.info(f"Starting AI-powered form filling for {job_title} at {company}")
            
            # Update the agent's task with specific instructions
            # Since we can't pass instructions to run(), we need to create a new agent with updated task
            from browser_use.llm import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.api_key
            )
            
            # Create a new agent with the specific instructions as the task
            specific_agent = Agent(
                task=instructions,
                llm=llm,
                page=page,
                use_vision=True,
                save_conversation_path="./logs/browser_use_conversations"
            )
            
            # Use browser-use agent to handle the form
            result = await specific_agent.run(max_steps=10)
            
            self.logger.info("Form filling completed successfully")
            
            # Check if the application was submitted
            page_content = await page.content()
            success_indicators = [
                "application submitted",
                "your application has been submitted",
                "application sent",
                "thank you for applying",
                "application received"
            ]
            
            if any(indicator in page_content.lower() for indicator in success_indicators):
                self.logger.info("Application appears to have been submitted successfully")
                return True
            else:
                self.logger.warning("Application may not have been fully submitted")
                return False
                
        except Exception as e:
            self.logger.error(f"Error handling application form: {str(e)}")
            return False
    
    async def handle_specific_question(self, page: Page, question: str) -> bool:
        """
        Handle a specific question or form section
        
        Args:
            page: Playwright page object  
            question: Specific question or instruction
            
        Returns:
            bool: True if handled successfully
        """
        try:
            if not self.agent:
                await self.initialize_agent(page)
                
            # Build targeted instructions for the specific question
            base_instructions = self._build_form_instructions()
            specific_instruction = f"""
Based on the following context about my background:

{base_instructions}

Please answer this specific question or handle this form section: {question}

Be precise and use the information provided above to give accurate answers.
"""
            
            # Create a new agent with the specific instruction as the task
            from browser_use.llm import ChatOpenAI
            
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=self.api_key
            )
            
            specific_agent = Agent(
                task=specific_instruction,
                llm=llm,
                page=page,
                use_vision=True,
                save_conversation_path="./logs/browser_use_conversations"
            )
            
            result = await specific_agent.run(max_steps=5)
            self.logger.info(f"Successfully handled specific question: {question}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling specific question '{question}': {str(e)}")
            return False
    
    async def close(self):
        """Clean up the agent"""
        if self.agent:
            try:
                await self.agent.close()
                self.logger.info("Browser-use agent closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing agent: {str(e)}")


# Helper function for integration with existing codebase
def create_form_handler(config: Dict[str, Any], openai_api_key: str) -> LinkedInFormHandler:
    """
    Factory function to create a LinkedIn form handler
    
    Args:
        config: Configuration dictionary from config.yaml
        openai_api_key: OpenAI API key
        
    Returns:
        LinkedInFormHandler: Configured form handler instance
    """
    return LinkedInFormHandler(config, openai_api_key)


# Example usage and testing
async def test_form_handler():
    """Test function for the form handler"""
    
    # Example config (normally loaded from config.yaml)
    test_config = {
        'personalInfo': {
            'First Name': 'John',
            'Last Name': 'Doe',
            'Mobile Phone Number': '555-0123',
            'Street address': '123 Main St',
            'City': 'New York, NY',
            'State': 'New York',
            'Zip': '10001',
            'Linkedin': 'linkedin.com/in/johndoe',
            'Website': 'github.com/johndoe'
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
            'default': 1
        },
        'industry': {
            'Engineering': 3,
            'default': 1
        },
        'universityGpa': '3.7',
        'languages': {
            'english': 'Native',
            'spanish': 'Conversational'
        }
    }
    
    # Note: You would need to provide your actual OpenAI API key
    api_key = "your-openai-api-key-here"
    
    handler = create_form_handler(test_config, api_key)
    print("Form handler created successfully!")
    print("Instructions preview:")
    print(handler._build_form_instructions())


if __name__ == "__main__":
    asyncio.run(test_form_handler())