import time, random, csv, pyautogui, pdb, traceback, sys, re, os
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from itertools import product


class LinkedinEasyApply:
    def __init__(self, parameters, driver):
        self.browser = driver
        self.email = parameters['email']
        self.password = parameters['password']
        self.disable_lock = parameters['disableAntiLock']
        self.blacklistDescriptionRegex = parameters.get('blacklistDescriptionRegex',[]) or []
        self.company_blacklist = parameters.get('companyBlacklist', []) or []
        self.title_blacklist = parameters.get('titleBlacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        self.file_name = "output"
        self.output_file_directory = parameters['outputFileDirectory']
        self.resume_dir = parameters['uploads']['resume']
        if 'coverLetter' in parameters['uploads']:
            self.cover_letter_dir = parameters['uploads']['coverLetter']
        else:
            self.cover_letter_dir = ''
        self.checkboxes = parameters.get('checkboxes', [])
        self.university_gpa = parameters['universityGpa']
        self.languages = parameters.get('languages', [])
        self.industry = parameters.get('industry', [])
        self.technology = parameters.get('technology', [])
        self.personal_info = parameters.get('personalInfo', [])
        self.eeo = parameters.get('eeo', [])
        self.technology_default = self.technology['default']
        self.industry_default = self.industry['default']
        
        # Create main debug folder structure
        self.main_debug_dir = "debug"
        if not os.path.exists(self.main_debug_dir):
            os.makedirs(self.main_debug_dir)
        
        # Create run-specific folder within main debug folder
        self.run_timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.main_debug_folder = os.path.join(self.main_debug_dir, f"run_{self.run_timestamp}")
        if not os.path.exists(self.main_debug_folder):
            os.makedirs(self.main_debug_folder)
        print(f"Created debug folder for this run: {self.main_debug_folder}")
        
        # Counter for failed applications in this run
        self.failed_application_count = 0


    def login(self):
        try:
            self.browser.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(5, 10))
            self.browser.find_element(By.ID, "username").send_keys(self.email)
            self.browser.find_element(By.ID, "password").send_keys(self.password)
            self.browser.find_element(By.CSS_SELECTOR, ".btn__primary--large").click()
            time.sleep(random.uniform(5, 10))
        except TimeoutException:
            raise Exception("Could not login!")

    def security_check(self):
        current_url = self.browser.current_url
        page_source = self.browser.page_source

        if '/checkpoint/challenge/' in current_url or 'security check' in page_source:
            input("Please complete the security check and press enter in this console when it is done.")
            time.sleep(random.uniform(5.5, 10.5))

    def start_applying(self):
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)

        page_sleep = 0
        minimum_time = 15*1     ## changed
        minimum_page_time = time.time() + minimum_time

        for (position, location) in searches:
            location_url = "&location=" + location
            job_page_number = -1

            print("Starting the search for " + position + " in " + location + ".")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    print("Going to job page " + str(job_page_number))
                    self.next_job_page(position, location_url, job_page_number)
                    time.sleep(random.uniform(1.5, 3.5))
                    print("Starting the application process for this page...")
                    self.apply_jobs(location)
                    print("Applying to jobs on this page has been completed!")

                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        print("Sleeping for " + str(time_left) + " seconds.")
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(120, 240) ## (500, 900)
                        print("Sleeping for " + str(sleep_time/60) + " minutes.")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except:
                traceback.print_exc()
                pass

            time_left = minimum_page_time - time.time()
            if time_left > 0:
                print("Sleeping for " + str(time_left) + " seconds.")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time
            if page_sleep % 5 == 0:
                sleep_time = random.randint(120, 240) ## (500, 900)
                print("Sleeping for " + str(sleep_time/60) + " minutes.")
                time.sleep(sleep_time)
                page_sleep += 1


    def apply_jobs(self, location):
        no_jobs_text = ""
        try:
            no_jobs_element = self.browser.find_element(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')
            no_jobs_text = no_jobs_element.text
        except:
            pass
        if 'No matching jobs found' in no_jobs_text:
            raise Exception("No more jobs on this page")

        if 'unfortunately, things aren' in self.browser.page_source.lower():
            raise Exception("No more jobs on this page")

        # Add debugging to save page source
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(self.browser.page_source)
        print(f"Current URL: {self.browser.current_url}")
        
        # Check if we're logged in properly
        if 'sign in' in self.browser.page_source.lower() or '/login' in self.browser.current_url.lower():
            print("Warning: May not be logged in properly")
            raise Exception("Login required or session expired")
        
        # Initialize job_list outside try block
        job_list = []
        
        try:
            # Wait for page to fully load with explicit wait
            wait = WebDriverWait(self.browser, 10)
            
            # Try multiple possible selectors for job results with WebDriverWait
            job_results = None
            selectors_to_try = [
                (By.CLASS_NAME, "jobs-search-results-list"),
                (By.CLASS_NAME, "scaffold-layout__list-container"),
                (By.CLASS_NAME, "jobs-search-results"),
                (By.CLASS_NAME, "jobs-search__results-list"),
                (By.CSS_SELECTOR, "[class*='jobs-search-results']"),
                (By.CSS_SELECTOR, "div.jobs-search__results-list"),
                (By.CSS_SELECTOR, "ul.scaffold-layout__list-container"),
                (By.CSS_SELECTOR, "[data-job-id]")  # Look for elements with job ID
            ]
            
            for by_type, selector in selectors_to_try:
                try:
                    job_results = wait.until(EC.presence_of_element_located((by_type, selector)))
                    print(f"Found job results using {by_type}: {selector}")
                    break
                except:
                    continue
            
            if not job_results:
                print("Could not find job results container after trying all selectors")
                # Try to find any list that might contain jobs
                try:
                    job_results = self.browser.find_element(By.CSS_SELECTOR, "ul")
                    print("Found a UL element as fallback")
                except:
                    raise Exception("Could not find any job search results on page")
            
            self.scroll_slow(job_results)
            self.scroll_slow(job_results, step=300, reverse=True)

            # Try multiple selectors for job list items
            
            # First try the most common selector - divs with data-job-id
            try:
                job_list = self.browser.find_elements(By.CSS_SELECTOR, "div[data-job-id]")
                if job_list:
                    print(f"Found {len(job_list)} jobs using div[data-job-id] selector")
            except:
                pass
            
            # If that didn't work, try other selectors
            if not job_list:
                item_selectors = [
                    (By.CLASS_NAME, "job-card-container"),
                    (By.CLASS_NAME, "jobs-search-results__list-item"),
                    (By.CLASS_NAME, "scaffold-layout__list-item"),
                    (By.CLASS_NAME, "jobs-search-results-list__list-item"),
                    (By.CSS_SELECTOR, "li[data-occludable-job-id]"),
                    (By.CSS_SELECTOR, ".job-card-list"),
                    (By.CSS_SELECTOR, "[class*='job-card-container']")
                ]
                
                for by_type, selector in item_selectors:
                    try:
                        job_list = self.browser.find_elements(by_type, selector)
                        if job_list:
                            print(f"Found {len(job_list)} jobs using {by_type}: {selector}")
                            break
                    except Exception as e:
                        continue
            
            # Debug: print first job element if found
            if job_list:
                print(f"Example job element HTML: {job_list[0].get_attribute('outerHTML')[:500]}...")
            else:
                print("No jobs found after trying all selectors")
                    
        except Exception as e:
            print(f"Error finding job results: {str(e)}")
            print(f"job_list has {len(job_list)} items")
            
        if len(job_list) == 0:
            print("job_list is empty, raising exception")
            raise Exception("No more jobs on this page")

        for job_tile in job_list:
            job_title, company, job_location, apply_method, link = "", "", "", "", ""

            # Try multiple selectors for job title
            try:
                # Try to find the link element which contains the title
                title_element = None
                try:
                    # Most common: link with job-card-list__title class
                    title_element = job_tile.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a.job-card-list__title--link, a[class*='job-card-container__link']")
                except:
                    try:
                        # Alternative: any link within artdeco-entity-lockup__title
                        title_element = job_tile.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title a")
                    except:
                        try:
                            # Fallback: any link with strong tag containing title
                            title_element = job_tile.find_element(By.CSS_SELECTOR, "a strong")
                        except:
                            pass
                
                if title_element:
                    job_title = title_element.text.strip()
                    link = title_element.get_attribute('href')
                    if link:
                        link = link.split('?')[0]
            except Exception as e:
                print(f"Error extracting job title: {str(e)}")
                pass
                
            # Try multiple selectors for company
            try:
                # Based on the HTML structure, company is in artdeco-entity-lockup__subtitle
                company_element = job_tile.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle, .job-card-container__company-name")
                company = company_element.text.strip()
            except:
                pass
                
            # Try multiple selectors for location
            try:
                # Location is typically in the first metadata item within caption
                location_element = job_tile.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__caption li:first-child, .job-card-container__metadata-item")
                job_location = location_element.text.strip()
            except:
                pass
            try:
                # Check for Easy Apply - look for the Easy Apply text or icon
                easy_apply_text = job_tile.find_elements(By.XPATH, ".//*[contains(text(), 'Easy Apply')]")
                if easy_apply_text:
                    apply_method = "Easy Apply"
                else:
                    # Alternative: check for LinkedIn bug icon which indicates Easy Apply
                    try:
                        job_tile.find_element(By.CSS_SELECTOR, "[data-test-icon='linkedin-bug-color-small']")
                        apply_method = "Easy Apply"
                    except:
                        apply_method = "Apply"
            except:
                apply_method = "Apply"

            contains_blacklisted_keywords = False
            job_title_parsed = job_title.lower().split(' ')

            for word in self.title_blacklist:
                if word.lower() in job_title_parsed:
                    contains_blacklisted_keywords = True
                    break

            if company.lower() not in [word.lower() for word in self.company_blacklist] and \
               contains_blacklisted_keywords is False and link not in self.seen_jobs:
                try:
                    # Try to find and click the job link element
                    job_el = None
                    try:
                        # Most common: link with job-card-list__title class or similar
                        job_el = job_tile.find_element(By.CSS_SELECTOR, "a.job-card-list__title, a.job-card-list__title--link, a[class*='job-card-container__link']")
                    except:
                        try:
                            # Alternative: any clickable link within the job tile
                            job_el = job_tile.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__title a")
                        except:
                            try:
                                # Fallback: click the job tile itself if it has data-job-id
                                if job_tile.get_attribute('data-job-id'):
                                    job_el = job_tile
                            except:
                                pass
                    
                    if job_el:
                        try:
                            # Try regular click first
                            job_el.click()
                        except:
                            try:
                                # If regular click fails, try JavaScript click
                                self.browser.execute_script("arguments[0].click();", job_el)
                            except:
                                print(f"Could not click on job: {job_title}")
                                continue
                    else:
                        print(f"Could not find clickable element for job: {job_title}")
                        continue

                    time.sleep(random.uniform(3, 5))
                    
                    
                    # Initialize inner_description with empty string
                    inner_description: str = ""
                    try:
                        # Try multiple selectors for job description
                        try:
                            inner_description = self.browser.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
                        except:
                            try:
                                inner_description = self.browser.find_element(By.CLASS_NAME, 'jobs-description__content').text
                            except:
                                try:
                                    inner_description = self.browser.find_element(By.CSS_SELECTOR, '[class*="jobs-description"]').text
                                except:
                                    print("Could not find job description")
                    except:
                        pass
                                        
                    contains_blacklisted_description_text: bool = False
                    if inner_description:  # Only check if we found a description
                        for sentence in self.blacklistDescriptionRegex:
                            match_result = re.search(sentence, inner_description, re.I)
                            is_in_description: bool = match_result is not None
                            if is_in_description:
                                contains_blacklisted_description_text = True
                                break

                    if contains_blacklisted_description_text:
                        print(f'Job description contains blacklisted text. {match_result}')
                    else:
                        try:
                            done_applying = self.apply_to_job(job_title, company)
                            if done_applying:
                                print("Done applying to the job!")
                            else:
                                print('Already applied to the job!')
                        except:
                            temp = self.file_name
                            self.file_name = "failed"
                            print("Failed to apply to job! Please submit a bug report with this link: " + link)
                            print("Writing to the failed csv file...")
                            try:
                                self.write_to_file(company, job_title, link, job_location, location)
                            except:
                                pass
                            self.file_name = temp

                        try:
                            self.write_to_file(company, job_title, link, job_location, location)
                        except Exception:
                            print("Could not write the job to the file! No special characters in the job title/company is allowed!")
                            traceback.print_exc()
                except Exception as e:
                    print(f"Error applying to job '{job_title}' at '{company}': {str(e)}")
                    if "no such element" in str(e).lower():
                        print("Element not found - LinkedIn may have changed their page structure")
                    traceback.print_exc()
                    pass
            else:
                print("Job contains blacklisted keyword or company name!")
            self.seen_jobs += link

    def create_debug_folder(self, job_title, company):
        """Create a debug subfolder for the failed job application within the main run folder"""
        # Increment the failed application counter
        self.failed_application_count += 1
        
        # Clean up job title and company for folder name
        safe_job_title = re.sub(r'[<>:"/\\|?*\n\r]', '_', job_title.strip())[:50]
        safe_company = re.sub(r'[<>:"/\\|?*\n\r]', '_', company.strip())[:30]
        
        # Create subfolder name with counter and timestamp
        app_timestamp = time.strftime("%H%M%S")
        subfolder_name = f"{self.failed_application_count:02d}_{safe_company}_{safe_job_title}_{app_timestamp}"
        
        # Create the full path within the main debug folder
        full_folder_path = os.path.join(self.main_debug_folder, subfolder_name)
        
        # Create the subfolder
        if not os.path.exists(full_folder_path):
            os.makedirs(full_folder_path)
        
        return full_folder_path

    def apply_to_job(self, job_title="Unknown", company="Unknown"):
        # Create debug folder for this application attempt
        debug_folder = None
        easy_apply_button = None

        try:
            # Try multiple selectors for the Easy Apply button
            easy_apply_button = self.browser.find_element(By.CLASS_NAME, 'jobs-apply-button')
        except:
            try:
                # Alternative selector
                easy_apply_button = self.browser.find_element(By.CSS_SELECTOR, "button[aria-label*='Easy Apply']")
            except:
                try:
                    # Another alternative
                    easy_apply_button = self.browser.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")
                except:
                    print("Could not find Easy Apply button")
                    return False

        try:
            job_description_area = self.browser.find_element(By.CLASS_NAME, "jobs-search__job-details--container")
            self.scroll_slow(job_description_area, end=1600)
            self.scroll_slow(job_description_area, end=1600, step=400, reverse=True)
        except:
            pass

        print("Applying to the job....")
        
        # Create debug folder only when we start applying (to avoid creating empty folders)
        debug_folder = self.create_debug_folder(job_title, company)
        print(f"Created debug folder: {debug_folder}")
        
        # Save page source before clicking Easy Apply
        with open(f'{debug_folder}/application_start.html', 'w', encoding='utf-8') as f:
            f.write(self.browser.page_source)
        print(f"Saved initial application page to {debug_folder}/application_start.html")
        
        easy_apply_button.click()
        
        # Wait for modal to appear and save it
        time.sleep(3)
        with open(f'{debug_folder}/application_modal.html', 'w', encoding='utf-8') as f:
            f.write(self.browser.page_source)
        print(f"Saved application modal page to {debug_folder}/application_modal.html")

        button_text = ""
        submit_application_text = 'submit application'
        while submit_application_text not in button_text.lower():
            retries = 3
            while retries > 0:
                try:
                    self.fill_up()
                    next_button = self.browser.find_element(By.CLASS_NAME, "artdeco-button--primary")
                    button_text = next_button.text.lower()
                    if submit_application_text in button_text:
                        try:
                            self.unfollow()
                        except:
                            print("Failed to unfollow company!")
                    time.sleep(random.uniform(1.5, 2.5))
                    next_button.click()
                    time.sleep(random.uniform(3.0, 5.0))

                    if 'please enter a valid answer' in self.browser.page_source.lower() or 'file is required' in self.browser.page_source.lower():
                        retries -= 1
                        print("Retrying application, attempts left: " + str(retries))
                        # Save page source when retry is needed
                        retry_count = 3 - retries
                        with open(f'{debug_folder}/failed_application_retry_{retry_count}.html', 'w', encoding='utf-8') as f:
                            f.write(self.browser.page_source)
                        print(f"Saved page source to {debug_folder}/failed_application_retry_{retry_count}.html")

                    else:
                        break
                except:
                    traceback.print_exc()
                    raise Exception("Failed to apply to job!")
            if retries == 0:
                print("All retries exhausted, saving final failed page")
                # Save the final failed page
                with open(f'{debug_folder}/failed_application_final.html', 'w', encoding='utf-8') as f:
                    f.write(self.browser.page_source)
                print(f"Saved final failed page to {debug_folder}/failed_application_final.html")
                
                traceback.print_exc()
                try:
                    self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
                    time.sleep(random.uniform(3, 5))
                    self.browser.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[1].click()
                    time.sleep(random.uniform(3, 5))
                except Exception as e:
                    print(f"Error closing modal: {str(e)}")
                raise Exception("Failed to apply to job!")

        closed_notification = False
        time.sleep(random.uniform(3, 5))
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            closed_notification = True
        except:
            pass
        try:
            self.browser.find_element(By.CLASS_NAME, 'artdeco-toast-item__dismiss').click()
            closed_notification = True
        except:
            pass
        time.sleep(random.uniform(3, 5))

        if closed_notification is False:
            raise Exception("Could not close the applied confirmation window!")

        return True

    def home_address(self, element):
        try:
            groups = element.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
            if len(groups) > 0:
                for group in groups:
                    lb = group.find_element(By.TAG_NAME, 'label').text.lower()
                    input_field = group.find_element(By.TAG_NAME, 'input')
                    if 'street' in lb:
                        self.enter_text(input_field, self.personal_info['Street address'])
                    elif 'city' in lb:
                        self.enter_text(input_field, self.personal_info['City'])
                        time.sleep(3)
                        input_field.send_keys(Keys.DOWN)
                        input_field.send_keys(Keys.RETURN)
                    elif 'zip' in lb or 'postal' in lb:
                        self.enter_text(input_field, self.personal_info['Zip'])
                    elif 'state' in lb or 'province' in lb:
                        self.enter_text(input_field, self.personal_info['State'])
                    else:
                        pass
        except:
            pass

    def get_answer(self, question):
        if self.checkboxes[question]:
            return 'yes'
        else:
            return 'no'

    def handle_new_form_structure(self):
        """Handle the new LinkedIn form structure with artdeco-text-input elements"""
        try:
            # Find all text input fields in the new structure
            text_inputs = self.browser.find_elements(By.CSS_SELECTOR, "input[class*='artdeco-text-input--input']")
            
            for input_field in text_inputs:
                try:
                    # Find the associated label
                    input_id = input_field.get_attribute('id')
                    label_element = self.browser.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    question_text = label_element.text.lower()
                    
                    print(f"Processing question: {question_text}")
                    
                    to_enter = ''
                    
                    # Check if it's a years of experience question
                    if ('how many years of work experience do you have with' in question_text or
                        'years of work experience' in question_text):
                        
                        # Extract the skill/technology from the question
                        skill_found = False
                        no_of_years = self.technology_default
                        
                        # Check against technology skills
                        for technology in self.technology:
                            if technology.lower() in question_text:
                                no_of_years = self.technology[technology]
                                skill_found = True
                                print(f"Found technology {technology}: {no_of_years} years")
                                break
                        
                        # Check against industry skills if no technology match
                        if not skill_found:
                            for industry in self.industry:
                                if industry.lower() in question_text:
                                    no_of_years = self.industry[industry]
                                    skill_found = True
                                    print(f"Found industry {industry}: {no_of_years} years")
                                    break
                        
                        to_enter = no_of_years
                        
                    elif 'grade point average' in question_text or 'gpa' in question_text:
                        to_enter = self.university_gpa
                    elif 'first name' in question_text:
                        to_enter = self.personal_info['First Name']
                    elif 'last name' in question_text:
                        to_enter = self.personal_info['Last Name']
                    elif 'phone' in question_text:
                        to_enter = self.personal_info['Mobile Phone Number']
                    else:
                        # For numeric fields, default to 0; for text fields, use a space
                        input_type = input_field.get_attribute('type')
                        if input_type == 'text' and 'numeric' in input_field.get_attribute('id'):
                            to_enter = 0
                        elif input_type == 'text':
                            to_enter = " ‏‏‎ "
                        else:
                            to_enter = 0
                    
                    # Clear the field first
                    input_field.clear()
                    
                    # Enter the value
                    if to_enter is not None and str(to_enter).strip():
                        input_field.send_keys(str(to_enter))
                        print(f"Entered '{to_enter}' for question: {question_text}")
                    
                except Exception as e:
                    print(f"Error processing input field: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error in handle_new_form_structure: {str(e)}")

    def additional_questions(self):
        #pdb.set_trace()
        frm_el = self.browser.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        
        # If the old structure doesn't exist, try the new structure
        if len(frm_el) == 0:
            print("Using new LinkedIn form structure...")
            self.handle_new_form_structure()
            return
            
        if len(frm_el) > 0:
            for el in frm_el:
                # Radio check
                try:
                    radios = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element').find_elements(By.CLASS_NAME, 'fb-radio')

                    radio_text = el.text.lower()
                    radio_options = [text.text.lower() for text in radios]
                    answer = "yes"

                    if 'driver\'s licence' in radio_text or 'driver\'s license' in radio_text:
                        answer = self.get_answer('driversLicence')
                    elif 'gender' in radio_text or 'veteran' in radio_text or 'race' in radio_text or 'disability' in radio_text or 'latino' in radio_text:
                        answer = ""
                        for option in radio_options:
                            if 'prefer' in option.lower() or 'decline' in option.lower() or 'don\'t' in option.lower() or 'specified' in option.lower() or 'none' in option.lower():
                                answer = option

                        if answer == "":
                            answer = radio_options[len(radio_options) - 1]
                    elif 'north korea' in radio_text:
                        answer = 'no'
                    elif 'sponsor' in radio_text:
                        answer = self.get_answer('requireVisa')
                    elif 'authorized' in radio_text or 'authorised' in radio_text or 'legally' in radio_text:
                        answer = self.get_answer('legallyAuthorized')
                    elif 'urgent' in radio_text:
                        answer = self.get_answer('urgentFill')
                    elif 'commuting' in radio_text:
                        answer = self.get_answer('commute')
                    elif 'background check' in radio_text:
                        answer = self.get_answer('backgroundCheck')
                    elif 'level of education' in radio_text:
                        for degree in self.checkboxes['degreeCompleted']:
                            if degree.lower() in radio_text:
                                answer = "yes"
                                break
                    elif 'level of education' in radio_text:
                        for degree in self.checkboxes['degreeCompleted']:
                            if degree.lower() in radio_text:
                                answer = "yes"
                                break
                    elif 'data retention' in radio_text:
                        answer = 'no'
                    else:
                        answer = radio_options[len(radio_options) - 1]

                    i = 0
                    to_select = None
                    for radio in radios:
                        if answer in radio.text.lower():
                            to_select = radios[i]
                        i += 1

                    if to_select is None:
                        to_select = radios[len(radios)-1]

                    self.radio_select(to_select, answer, len(radios) > 2)

                    if radios != []:
                        continue
                except:
                    pass
                # Questions check
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    question_text = question.find_element(By.CLASS_NAME, 'fb-form-element-label').text.lower()

                    txt_field_visible = False
                    try:
                        txt_field = question.find_element(By.CLASS_NAME, 'fb-single-line-text__input')

                        txt_field_visible = True
                    except:
                        try:
                            txt_field = question.find_element(By.CLASS_NAME, 'fb-textarea')

                            txt_field_visible = True
                        except:
                            pass

                    if txt_field_visible != True:
                        txt_field = question.find_element(By.CLASS_NAME, 'multi-line-text__input')

                    text_field_type = txt_field.get_attribute('name').lower()
                    if 'numeric' in text_field_type:
                        text_field_type = 'numeric'
                    elif 'text' in text_field_type:
                        text_field_type = 'text'

                    to_enter = ''
                    if ('experience do you currently have' in question_text or 'many years of working experience do you have' in question_text):
                        no_of_years = self.industry_default

                        for industry in self.industry:
                            if industry.lower() in question_text:
                                no_of_years = self.industry[industry]
                                break

                        to_enter = no_of_years
                    elif ('many years of work experience do you have using' in question_text or 
                          'many years of work experience do you have with' in question_text or
                          'how many years of work experience do you have with' in question_text):
                        no_of_years = self.technology_default

                        for technology in self.technology:
                            if technology.lower() in question_text:
                                no_of_years = self.technology[technology]
                                break

                        to_enter = no_of_years
                    elif 'grade point average' in question_text:
                        to_enter = self.university_gpa
                    elif 'first name' in question_text:
                        to_enter = self.personal_info['First Name']
                    elif 'last name' in question_text:
                        to_enter = self.personal_info['Last Name']
                    elif 'name' in question_text:
                        to_enter = self.personal_info['First Name'] + " " + self.personal_info['Last Name']
                    elif 'phone' in question_text:
                        to_enter = self.personal_info['Mobile Phone Number']
                    elif 'linkedin' in question_text:
                        to_enter = self.personal_info['Linkedin']
                    elif 'website' in question_text or 'github' in question_text or 'portfolio' in question_text:
                        to_enter = self.personal_info['Website']
                    else:
                        if text_field_type == 'numeric':
                            to_enter = 0
                        else:
                            to_enter = " ‏‏‎ "

                    if text_field_type == 'numeric':
                        if not isinstance(to_enter, (int, float)):
                            to_enter = 0
                    elif to_enter == '':
                        to_enter = " ‏‏‎ "

                    self.enter_text(txt_field, to_enter)
                    continue
                except:
                    pass
                # Date Check
                try:
                    date_picker = el.find_element(By.CLASS_NAME, 'artdeco-datepicker__input ')
                    date_picker.clear()
                    date_picker.send_keys(date.today().strftime("%m/%d/%y"))
                    time.sleep(3)
                    date_picker.send_keys(Keys.RETURN)
                    time.sleep(2)
                    continue
                except:
                    pass
                # Dropdown check
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
                    question_text = question.find_element(By.CLASS_NAME, 'fb-form-element-label').text.lower()

                    dropdown_field = question.find_element(By.CLASS_NAME, 'fb-dropdown__select')

                    select = Select(dropdown_field)

                    options = [options.text for options in select.options]

                    if 'proficiency' in question_text:
                        proficiency = "Conversational"

                        for language in self.languages:
                            if language.lower() in question_text:
                                proficiency = self.languages[language]
                                break

                        self.select_dropdown(dropdown_field, proficiency)
                    elif 'country code' in question_text:
                        self.select_dropdown(dropdown_field, self.personal_info['Phone Country Code'])
                    elif 'united states' in question_text:

                        choice = ""

                        for option in options:
                            if 'no' in option.lower():
                                choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    elif 'sponsor' in question_text:
                        answer = self.get_answer('requireVisa')

                        choice = ""

                        for option in options:
                            if answer == 'yes':
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    elif 'authorized' in question_text or 'authorised' in question_text:
                        answer = self.get_answer('legallyAuthorized')

                        choice = ""

                        for option in options:
                            if answer == 'yes':
                                # find some common words
                                choice = option
                            else:
                                if 'no' in option.lower():
                                    choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    elif 'citizenship' in question_text:
                        answer = self.get_answer('legallyAuthorized')

                        choice = ""

                        for option in options:
                            if answer == 'yes':
                                if 'no' in option.lower():
                                    choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    elif 'gender' in question_text or 'veteran' in question_text or 'race' in question_text or 'disability' in question_text or 'latino' in question_text:

                        choice = ""

                        for option in options:
                            if 'prefer' in option.lower() or 'decline' in option.lower() or 'don\'t' in option.lower() or 'specified' in option.lower() or 'none' in option.lower():
                                choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    else:
                        choice = ""

                        for option in options:
                            if 'yes' in option.lower():
                                choice = option

                        if choice == "":
                            choice = options[len(options) - 1]

                        self.select_dropdown(dropdown_field, choice)
                    continue
                except:
                    pass

                # Checkbox check for agreeing to terms and service
                try:
                    question = el.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')

                    clickable_checkbox = question.find_element(By.TAG_NAME, 'label')

                    clickable_checkbox.click()
                except:
                    pass

    def unfollow(self):
        try:
            follow_checkbox = self.browser.find_element(By.XPATH, "//label[contains(.,\'to stay up to date with their page.\')]").click()
            follow_checkbox.click()
        except:
            pass

    def send_resume(self):
        try:
            file_upload_elements = (By.CSS_SELECTOR, "input[name='file']")
            if len(self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])) > 0:
                input_buttons = self.browser.find_elements(file_upload_elements[0], file_upload_elements[1])
                for upload_button in input_buttons:
                    upload_type = upload_button.find_element(By.XPATH, "..").find_element(By.XPATH, "preceding-sibling::*")
                    if 'resume' in upload_type.text.lower():
                        upload_button.send_keys(self.resume_dir)
                    elif 'cover' in upload_type.text.lower():
                        if self.cover_letter_dir != '':
                            upload_button.send_keys(self.cover_letter_dir)
                        elif 'required' in upload_type.text.lower():
                            upload_button.send_keys(self.resume_dir)
        except:
            print("Failed to upload resume or cover letter!")
            pass


    def enter_text(self, element, text):
        element.clear()
        element.send_keys(text)

    def select_dropdown(self, element, text):
        select = Select(element)
        select.select_by_visible_text(text)

    # Radio Select
    def radio_select(self, element, label_text, clickLast=False):
        label = element.find_element(By.TAG_NAME, 'label')
        if label_text in label.text.lower() or clickLast == True:
            label.click()
        else:
            pass

    # Contact info fill-up
    def contact_info(self):
        frm_el = self.browser.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        if len(frm_el) > 0:
            for el in frm_el:
                text = el.text.lower()
                if 'email address' in text:
                    continue
                elif 'phone number' in text:
                    try:
                        country_code_picker = el.find_element(By.CLASS_NAME, 'fb-dropdown__select')
                        self.select_dropdown(country_code_picker, self.personal_info['Phone Country Code'])
                    except:
                        print("Country code " + self.personal_info['Phone Country Code'] + " not found! Make sure it is exact.")
                    try:
                        phone_number_field = el.find_element(By.CLASS_NAME, 'fb-single-line-text__input')
                        self.enter_text(phone_number_field, self.personal_info['Mobile Phone Number'])
                    except:
                        print("Could not input phone number.")

    def fill_up(self):
        try:
            easy_apply_content = self.browser.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
            b4 = easy_apply_content.find_element(By.CLASS_NAME, 'pb4')
            pb4 = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
            if len(pb4) > 0:
                for pb in pb4:
                    try:
                        label = pb.find_element(By.TAG_NAME, 'h3').text.lower()
                        try:
                            self.additional_questions()
                        except:
                            pass

                        try:
                            self.send_resume()
                        except:
                            pass

                        if 'home address' in label:
                            self.home_address(pb)
                        elif 'contact info' in label:
                            self.contact_info()
                    except:
                        pass
        except:
            pass

    def write_to_file(self, company, job_title, link, location, search_location):
        to_write = [company, job_title, link, location]
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        file_path = self.output_file_directory + self.file_name + search_location + ".csv"

        with open(file_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(to_write)

    def scroll_slow(self, scrollable_element, start=0, end=3600, step=100, reverse=False):
        if reverse:
            start, end = end, start
            step = -step

        for i in range(start, end, step):
            self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollable_element)
            time.sleep(random.uniform(1.0, 2.6))

    def avoid_lock(self):
        if self.disable_lock:
            return

        pyautogui.keyDown('ctrl')
        pyautogui.press('esc')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        pyautogui.press('esc')

    def get_base_search_url(self, parameters):
        remote_url = ""

        if parameters['remote']:
            remote_url = "f_CF=f_WRA"

        level = 1
        experience_level = parameters.get('experienceLevel', [])
        experience_url = "f_E="
        for key in experience_level.keys():
            if experience_level[key]:
                experience_url += "%2C" + str(level)
            level += 1

        distance_url = "?distance=" + str(parameters['distance'])

        job_types_url = "f_JT="
        job_types = parameters.get('experienceLevel', [])
        for key in job_types:
            if job_types[key]:
                job_types_url += "%2C" + key[0].upper()

        date_url = ""
        dates = {"all time": "", "month": "&f_TPR=r2592000", "week": "&f_TPR=r604800", "24 hours": "&f_TPR=r86400"}
        date_table = parameters.get('date', [])
        for key in date_table.keys():
            if date_table[key]:
                date_url = dates[key]
                break

        easy_apply_url = "&f_LF=f_AL"

        extra_search_terms = [distance_url, remote_url, job_types_url, experience_url]
        extra_search_terms_str = '&'.join(term for term in extra_search_terms if len(term) > 0) + easy_apply_url + date_url

        return extra_search_terms_str

    def next_job_page(self, position, location, job_page):
        self.browser.get("https://www.linkedin.com/jobs/search/" + self.base_search_url +
                         "&keywords=" + position + location + "&start=" + str(job_page*25))

        self.avoid_lock()

