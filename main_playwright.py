#!/usr/bin/env python3
"""
Main entry point for Playwright-based LinkedIn Easy Apply Bot
Single browser architecture with integrated AI form handling
"""

import asyncio
import yaml
import sys
import logging
from pathlib import Path
from validate_email import validate_email
from playwright_linkedin_bot import PlaywrightLinkedInBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_yaml():
    """Validate configuration file"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml file not found!")
    
    with open(config_path, 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    mandatory_params = [
        'email', 'password', 'disableAntiLock', 'remote', 'experienceLevel', 
        'jobTypes', 'date', 'positions', 'locations', 'distance', 
        'outputFileDirectory', 'checkboxes', 'universityGpa', 'languages', 
        'industry', 'technology', 'personalInfo', 'eeo', 'uploads', 
        'blacklistDescriptionRegex'
    ]

    for mandatory_param in mandatory_params:
        if mandatory_param not in parameters:
            raise Exception(f'{mandatory_param} is not inside the yml file!')

    # Validate email format
    assert validate_email(parameters['email']), "Invalid email format"
    assert len(str(parameters['password'])) > 0, "Password cannot be empty"
    assert isinstance(parameters['disableAntiLock'], bool), "disableAntiLock must be boolean"
    assert isinstance(parameters['remote'], bool), "remote must be boolean"

    # Validate experience level
    assert len(parameters['experienceLevel']) > 0, "experienceLevel cannot be empty"
    experience_level = parameters.get('experienceLevel', {})
    assert any(experience_level.values()), "At least one experience level must be selected"

    # Validate job types
    assert len(parameters['jobTypes']) > 0, "jobTypes cannot be empty"
    job_types = parameters.get('jobTypes', {})
    assert any(job_types.values()), "At least one job type must be selected"

    # Validate date filter
    assert len(parameters['date']) > 0, "date filter cannot be empty"
    date_filter = parameters.get('date', {})
    assert any(date_filter.values()), "At least one date filter must be selected"

    # Validate distance
    approved_distances = {0, 5, 10, 25, 50, 100}
    assert parameters['distance'] in approved_distances, f"Distance must be one of {approved_distances}"

    # Validate positions and locations
    assert len(parameters['positions']) > 0, "positions cannot be empty"
    assert len(parameters['locations']) > 0, "locations cannot be empty"

    # Validate uploads
    assert len(parameters['uploads']) >= 1 and 'resume' in parameters['uploads'], "resume upload is required"

    # Validate checkboxes
    assert len(parameters['checkboxes']) > 0, "checkboxes cannot be empty"
    checkboxes = parameters.get('checkboxes', {})
    required_checkbox_fields = [
        'driversLicence', 'requireVisa', 'legallyAuthorized', 
        'urgentFill', 'commute', 'backgroundCheck'
    ]
    for field in required_checkbox_fields:
        assert isinstance(checkboxes.get(field), bool), f"{field} must be boolean"
    assert 'degreeCompleted' in checkboxes, "degreeCompleted is required in checkboxes"

    # Validate GPA
    assert isinstance(parameters['universityGpa'], (int, float)), "universityGpa must be a number"

    # Validate languages
    languages = parameters.get('languages', {})
    language_types = {'none', 'conversational', 'professional', 'native or bilingual'}
    for language in languages:
        assert languages[language].lower() in language_types, f"Invalid language level for {language}"

    # Validate industry experience
    industry = parameters.get('industry', {})
    for skill in industry:
        assert isinstance(industry[skill], int), f"Industry experience for {skill} must be integer"
    assert 'default' in industry, "default industry experience is required"

    # Validate technology experience
    technology = parameters.get('technology', {})
    for tech in technology:
        assert isinstance(technology[tech], int), f"Technology experience for {tech} must be integer"
    assert 'default' in technology, "default technology experience is required"

    # Validate personal info
    assert len(parameters['personalInfo']) > 0, "personalInfo cannot be empty"
    personal_info = parameters.get('personalInfo', {})
    for info in personal_info:
        assert personal_info[info] != '', f"personalInfo.{info} cannot be empty"

    # Validate EEO
    assert len(parameters['eeo']) > 0, "eeo cannot be empty"
    eeo = parameters.get('eeo', {})
    for survey_question in eeo:
        assert eeo[survey_question] != '', f"eeo.{survey_question} cannot be empty"

    logger.info("✅ Configuration validation successful")
    return parameters


async def main():
    """Main async function"""
    try:
        logger.info("🚀 Starting Playwright LinkedIn Easy Apply Bot")
        
        # Validate configuration
        parameters = validate_yaml()
        
        # Create bot instance
        bot = PlaywrightLinkedInBot(parameters)
        
        # Display configuration summary
        logger.info("📋 Configuration Summary:")
        logger.info(f"   📧 Email: {parameters['email']}")
        logger.info(f"   🎯 Positions: {', '.join(parameters['positions'][:3])}")
        logger.info(f"   📍 Locations: {', '.join(parameters['locations'][:3])}")
        logger.info(f"   🤖 AI Forms: {'Enabled' if parameters.get('useAIForms', True) else 'Disabled'}")
        logger.info(f"   🔧 Mode: {parameters.get('formHandlingMode', 'ai-only')}")
        
        try:
            # Initialize browser
            success = await bot.initialize_browser()
            if not success:
                raise Exception("Failed to initialize browser")
            
            # Initialize AI agent
            await bot.initialize_ai_agent()
            
            # Start the application process
            await bot.login()
            await bot.security_check()
            await bot.start_applying()
            
        finally:
            # Always clean up resources
            await bot.cleanup()
            
        # Print final statistics
        bot.print_ai_stats()
        logger.info("🎉 Bot execution completed successfully")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def check_requirements():
    """Check if required packages are installed"""
    try:
        import playwright
        import browser_use
        import yaml
        import validate_email
        logger.info("✅ All required packages are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.error("Please install missing packages:")
        logger.error("pip install playwright browser-use pyyaml validate-email")
        logger.error("playwright install")
        return False


if __name__ == '__main__':
    # Check requirements first
    if not check_requirements():
        sys.exit(1)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
        sys.exit(0)