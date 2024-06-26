import time

import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import (check_element_text_is_empty,
                   convert_strdate_to_numbpad_keys,
                   today_date_in_keys)
import yaml

from webdrivers_installer import install_web_driver

from selenium.webdriver.chrome.service import Service as ChromeService
import webdriver_manager.chrome as ChromeDriverManager
ChromeDriverManager = ChromeDriverManager.ChromeDriverManager


class PageStep:
    def __init__(self, action, params, options=None):
        self.action = action
        self.params = params
        if options is None:
            self.options = {}
        else:
            self.options = options

def browser_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")
    #options.add_argument(r'--remote-debugging-port=9222')
    #options.add_argument(r'--profile-directory=Person 1')

    # Disable webdriver flags or you will be easily detectable
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Load user profile
    #options.add_argument(r"--user-data-dir={}".format(self.profile_path))
    return options

class WorkdayAutofill:
    def __init__(self, application_link, resume_path):
        self.application_link = application_link
        self.resume_path = resume_path
        self.driver = WorkdayAutofill.create_webdriver("chrome")
        self.resume_data = self.load_resume()
        self.current_url = None
        self.ELEMENT_WAITING_TIMEOUT = 3

 

    @classmethod
    def create_webdriver(cls, browser_name):
        try:
            if browser_name.lower() == "firefox":
                driver = webdriver.Firefox()
            elif browser_name.lower() == "chrome":
                driver = webdriver.Chrome()
            else:
                raise RuntimeError(f"{browser_name} is not supported !")
        except selenium_exceptions.WebDriverException:
            # trying to install the web driver if not installed in the system
            if browser_name.lower() == "firefox":
                web_driver_path = install_web_driver(requested_browser=browser_name)
                driver = webdriver.Firefox(service=FirefoxService(executable_path=web_driver_path))
                return driver
            elif browser_name.lower() == "chrome":
                # web_driver_path = install_web_driver(requested_browser=browser_name)
                # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=browser_options())
                print(driver)
                return driver
                # driver = webdriver.Chrome(service=ChromeService(executable_path=web_driver_path))
            else:
                raise RuntimeError(f"{browser_name} is not supported !")
        else:
            return driver

    def load_resume(self):
        with open(self.resume_path) as resume:
            try:
                return yaml.safe_load(resume)
            except yaml.YAMLError as e:
                print(e)

    def load_work_experiences(self):
        try:
            works = self.resume_data["my-experience"]["work-experiences"]
            return [work_dict[f"work{idx}"] for idx, work_dict in enumerate(works, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml WORK-EXPERIENCE"
                             f" -> please review the works order !")

    def load_education_experiences(self):
        try:
            educations = self.resume_data["my-experience"]["education-experiences"]
            return [education_dict[f"education{idx}"] for idx, education_dict in enumerate(educations, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml EDUCATION-EXPERIENCES"
                             f" -> please review the educations order !")

    def load_languages(self):
        try:
            languages = self.resume_data["my-experience"]["languages"]
            return [language_dict[f"language{idx}"] for idx, language_dict in enumerate(languages, start=1)]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml LANGUAGES"
                             f" -> please review the languages order !")

    def load_additional_information(self):
        try:
            return self.resume_data["additional-information"]
        except KeyError:
            raise ValueError("Something went wrong while parsing your resume.yml LANGUAGES"
                             f" -> please review the additional-information key !")

    def locate_and_fill(self, element_xpath, input_data, kwoptions):
        if not input_data:
            return False
        if not kwoptions.get("required"):
            try:
                element = self.driver.find_element(By.XPATH, element_xpath)
            except selenium_exceptions.NoSuchElementException:
                # skip if element is not in the page
                return False
        else:
            try:
                element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, element_xpath)))
            except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
                raise RuntimeError(
                    f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
                )
        if kwoptions.get("only_if_empty") and not check_element_text_is_empty(element):
            # quit if the element is already filled
            return False
        # fill date MM/YYYY
        if "YYYY" in element_xpath:
            date_keys = convert_strdate_to_numbpad_keys(input_data)
            element.send_keys(date_keys)
        else:
            time.sleep(.1)
            self.driver.execute_script(
                'arguments[0].value="";', element)
            time.sleep(.1)
            element.send_keys(input_data)
            time.sleep(.1)
        if kwoptions.get("press_enter"):
            element.send_keys(Keys.ENTER)
        return True

    def locate_dropdown_and_fill(self, element_xpath, input_data, kwoptions):
        if not kwoptions.get("required"):
            try:
                element = self.driver.find_element(By.XPATH, element_xpath)
            except selenium_exceptions.NoSuchElementException:
                # skip if element is not in the page
                return False
        else:
            try:
                element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, element_xpath)))
            except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
                raise RuntimeError(
                    f"Cannot locate element '{element_xpath}' in the following page : {self.driver.current_url}"
                )

        self.driver.execute_script("arguments[0].click();", element)
        time.sleep(.3)
        element.send_keys(input_data)
        time.sleep(.3)
        from selenium.webdriver.common.keys import Keys 
        element.send_keys(Keys.ENTER)
        time.sleep(.3)
        if kwoptions.get("value_is_pattern"):
            select_xpath = f'//*[@id="1"]'
        else:
            select_xpath = f'//*[@id="2"]'
        try:
            choice = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, select_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            print(
                f"Cannot locate option: >'{input_data}'< in the following drop down : {element_xpath}"
                " Check your resume data"
            )
            return True
        else:
            self.driver.execute_script("arguments[0].click();", choice)
            time.sleep(.3)
            from selenium.webdriver.common.keys import Keys 
            element = self.driver.switch_to.active_element
            element.send_keys(Keys.ESCAPE) 
            time.sleep(2)
            return True

    def locate_and_click(self, button_xpath, kwoptions):
        try:
            clickable_element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            if not kwoptions.get("required"):
                return True
            raise RuntimeError(
                f"Cannot locate submit button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", clickable_element)
            time.sleep(1)
            return True

    def locate_and_upload(self, button_xpath, file_location):
        try:
            element = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, button_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate button '{button_xpath}' in the following page : {self.driver.current_url}"
            )
        else:
            element.send_keys(file_location)
            return True

    def locate_and_drag_drop(self, element1_xpath, element2_xpath):
        try:
            element1 = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element1_xpath)))
            element2 = WebDriverWait(self.driver, self.ELEMENT_WAITING_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, element2_xpath)))
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            raise RuntimeError(
                f"Cannot locate '{element1_xpath}' or '{element2_xpath}'  in the following page : "
                f"{self.driver.current_url}"
            )
        else:
            action = ActionChains(self.driver)
            action.drag_and_drop(element1, element2).perform()
            return True

    def execute_instructions(self, instructions):
        while(instructions):
            for idx, page_step in enumerate(instructions):

                if page_step.action == "LOCATE_AND_FILL":
                    status = self.locate_and_fill(*page_step.params, page_step.options)
                elif page_step.action == "LOCATE_AND_CLICK":
                    status = self.locate_and_click(*page_step.params, page_step.options)
                elif page_step.action == "LOCATE_DROPDOWN_AND_FILL":
                    status = self.locate_dropdown_and_fill(*page_step.params, page_step.options)
                elif page_step.action == "LOCATE_AND_UPLOAD":
                    status = self.locate_and_upload(*page_step.params, page_step.options)
                elif page_step.action == "LOCATE_AND_DRAG_DROP":
                    status = self.locate_and_drag_drop(*page_step.params, page_step.options)
                else:
                    raise RuntimeError(f"Unknown instruction: {page_step.action} \n"
                                    f" called with params : {page_step.params} \n "
                                    f"and options : {page_step.options} ")
                # remove the element if he got filled
                if status:
                    instructions.pop(idx)
                time.sleep(1)

    def execute_instructions2(self, instructions):
        while(instructions):
            page_step = instructions.popleft()
            
            if page_step.action == "LOCATE_AND_FILL":
                status = self.locate_and_fill(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_CLICK":
                status = self.locate_and_click(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_DROPDOWN_AND_FILL":
                status = self.locate_dropdown_and_fill(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_UPLOAD":
                status = self.locate_and_upload(*page_step.params, page_step.options)
            elif page_step.action == "LOCATE_AND_DRAG_DROP":
                status = self.locate_and_drag_drop(*page_step.params, page_step.options)
            else:
                raise RuntimeError(f"Unknown instruction: {page_step.action} \n"
                                f" called with params : {page_step.params} \n "
                                f"and options : {page_step.options} ")
            # remove the element if he got filled
            if not status:
                instructions.append(page_step)
            time.sleep(1)

    def login(self):
        email_xpath = '//*[@id="input-4"]'
        password_xpath = '//*[@id="input-5"]'  # Updated XPath
        submit_xpath = '//div[contains(@aria-label,"Sign In")]'
        email = self.resume_data["account"]["email"]
        password = self.resume_data["account"]["password"]
        print(password)
        self.execute_instructions([
            # locate email input & fill
            PageStep(action="LOCATE_AND_FILL",
                    params=[email_xpath, email],
                    options={
                        "required": True
                    }),
            # locate password input & fill
            # PageStep(action="LOCATE_AND_FILL",
            #         params=[password_xpath, password],
            #         options={
            #             "required": True
            #         }
            #         )
        ])

        self.execute_instructions([
            PageStep(action="LOCATE_AND_FILL",
                    params=[password_xpath, password],
                    options={
                        "required": True
                    }
                    ),
        ])                

        # submit
        self.execute_instructions([
            PageStep(action="LOCATE_AND_CLICK",
                    params=[submit_xpath])
        ])

    def fill_my_information_page(self):
        # Previous work
        if self.resume_data["my-information"]["previous-work"]:
            previous_work_xpath = '//*[@id="1"]'

        else:
            previous_work_xpath = '//*[@id="input-2"]/div[2]/label'
            

        # instructions List of ordered steps :
        # a list of (Action, HTML Xpath, Value, options ...)
        # options is not required
        instructions = [
            # How Did You Hear About Us
            (PageStep(action="LOCATE_AND_FILL",
                      params=['//div//text()[contains(., "How Did You Hear About Us?")]'
                              '/following::input[1]',
                              self.resume_data["my-information"]["source"]],
                      options={"press_enter": True})),
            # Country
            
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=['//div//text()[contains(., "Country")]'
                             '/following::button[@aria-haspopup="listbox"][1]',
                             self.resume_data["my-information"]["country"]]),
            
            # Previous work
            PageStep(action="LOCATE_AND_CLICK",
                     params=[previous_work_xpath]),

            # # First Name
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "First Name")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["first-name"]]),
            # Last Name
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Last Name")]'
                             '/following::input[1]',
                             self.resume_data["my-information"]["last-name"]]),
            
            # ****** Legal Name ******
            # ****** Address ******
            # Line 1
            # PageStep(action="LOCATE_AND_FILL",
            #          params=['//div[@data-automation-id="addressSection"]'
            #                  '//text()[contains(., "Address Line 1")]'
            #                  '/following::input[1]',
            #                  self.resume_data["my-information"]["address-line"]]),
            # # City
            # PageStep(action="LOCATE_AND_FILL",
            #          params=['//div[@data-automation-id="addressSection"]'
            #                  '//text()[contains(., "City")]'
            #                  '/following::input[1]',
            #                  self.resume_data["my-information"]["city"]]),
            # # State
            # PageStep(action="LOCATE_DROPDOWN_AND_FILL",
            #          params=['//div[@data-automation-id="addressSection"]'
            #                  '//text()[contains(., "State")]'
            #                  '/following::button[@aria-haspopup="listbox"][1]',
            #                  self.resume_data["my-information"]["state"]]),
            # # Zip
            # PageStep(action="LOCATE_AND_FILL",
            #          params=['//div[@data-automation-id="addressSection"]'
            #                  '//text()[contains(., "Postal Code")]'
            #                  '/following::input[1]',
            #                  self.resume_data["my-information"]["zip"]]),

            # ****** Phone ******
            # Phone Code
            # PageStep(action="LOCATE_AND_FILL",
            #          params=['//div//text()[contains(., "Country Phone Code")]/following::input[1]',
            #                  self.resume_data["my-information"]["phone-code-country"]],
            #          options={'press_enter': True}),
            # Device Type
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Phone Device Type")]'
                             '/following::button[@aria-haspopup="listbox"][1]',
                             self.resume_data["my-information"]["phone-device-type"]],
                             ),

            # Number
            PageStep(action="LOCATE_AND_FILL",
                     params=['//div//text()[contains(., "Phone Number")]/following::input[1]',
                             self.resume_data["my-information"]["phone-number"]]),
            # Extension
            # PageStep(action="LOCATE_AND_FILL",
            #          params=['//div//text()[contains(., "Phone Extension")]'
            #                  '/following::input[1]',
            #                  self.resume_data["my-information"]["phone-extension"]]),
            
            # # Submit
            PageStep(action="LOCATE_AND_CLICK",
                     params=['//div//button[contains(text(),"Save and Continue")]']),
        ]

        self.execute_instructions(instructions.copy())

    def add_works(self, instructions):
        # check if there are work experiences
        if len(self.load_work_experiences()):
            # click ADD button
            instructions.append(PageStep(action="LOCATE_AND_CLICK",
                                         params=[
                                             '//button[@aria-label="Add Work Experience" and @data-automation-id="Add"]']))
            # fill work experiences
            works_count = len(self.load_work_experiences())
            for idx, work in enumerate(self.load_work_experiences(), start=1):
                instructions += [
                    # Job title
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Job Title")]'
                                     f'/following::Input[1]',
                                     work["job-title"]]),
                    # Company
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Company")]'
                                     f'/following::Input[1]',
                                     work["company"]]),
                    # Location
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Location")]/following::Input[1]',
                                     work["location"]]),
                    # From Date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"From")]'
                                     f'/following::input[contains(@aria-valuetext, "MM") '
                                     f'or contains(@aria-valuetext, "YYYY")][1]',
                                     work["from"]]),
                    # Description
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                     f'/following::text()[contains(.,"Role Description")]'
                                     f'/following::textarea[1]',
                                     work["description"]])
                ]
                # Current work
                if not work["current-work"]:
                    # To Date
                    instructions.append(PageStep(action="LOCATE_AND_FILL",
                                                 params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                                         '/following::text()[contains(.,"To")]'
                                                         '/following::input[contains(@aria-valuetext, "MM") or '
                                                         'contains(@aria-valuetext, "YYYY") ][1]', work["to"]]))

                else:
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Work Experience {idx}")]'
                                         '/following::text()[contains(.,"I currently work here")]'
                                         '/following::input[1]']),
                    )
                # check if more work experiences remaining
                if not idx == works_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//div//text()[contains(.,"Work Experience {idx}")]'
                                         '/following::button[contains(text(),"Add Another")]']),
                    )
        return instructions

    def add_education(self, instructions):
        # check if there are education experiences
        if len(self.load_education_experiences()):
            # click add button if not initialized
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Education")]'
                                 '/following::button[contains(text(),"Add")][1]'])
            )

            # fill work experiences
            educations_count = len(self.load_education_experiences())
            for idx, education in enumerate(self.load_education_experiences(), start=1):
                instructions += [
                    # School or University
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"School or University")]'
                                     f'/following::input[1]',
                                     education["university"]]),
                    # Degree
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"Degree")]'
                                     f'/following::button[1]',
                                     education["degree"]],
                             options={
                                 "value_is_pattern": True
                             }),
                    # Field of study
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"Field of Study")]'
                                     f'/following::input[1]',
                                     education["field-of-study"]],
                             options={"press_enter": True}),
                    # # Gpa
                    # PageStep(action="LOCATE_AND_FILL",
                    #          params=[f'//text()[contains(.,"Education {idx}")]'
                    #                  '/following::text()[contains(.,"Overall Result")]/'
                    #                  'following::input[1]',
                    #                  education["gpa"]]),
                    # From date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     '/following::text()[contains(.,"From")]/'
                                     'following::input[contains(@aria-valuetext, "MM")'
                                     ' or contains(@aria-valuetext, "YYYY") ][1]',
                                     education["from"]]),

                    # To date
                    PageStep(action="LOCATE_AND_FILL",
                             params=[f'//text()[contains(.,"Education {idx}")]'
                                     f'/following::text()[contains(.,"To")]'
                                     f'/following::input[contains(@aria-valuetext, "MM")'
                                     f' or contains(@aria-valuetext, "YYYY") ][1]',
                                     education["to"]]),
                ]

                # check if more education experiences remaining
                if not idx == educations_count:
                    # Add another
                    instructions.append(PageStep(action="LOCATE_AND_CLICK",
                                                 params=[f'//text()[contains(.,"Education {idx}")]'
                                                         f'/following::button[contains(text(),"Add Another")][1]']))
        return instructions

    def add_resume(self, instructions):
        instructions += [
            # delete the old resume if exist
            PageStep(action="LOCATE_AND_CLICK",
                     params=['//button[@data-automation-id="delete-file"]']),
            PageStep(action="LOCATE_AND_FILL",
                     params=['//input[@data-automation-id="file-upload-input-ref"]',
                             self.resume_data["my-experience"]["resume"]]),
            PageStep(action="LOCATE_AND_CLICK",
                    params=[
                        '//button[contains(text(),"Save and Continue")]'])
        ]
        return instructions

    def check_section_exist(self, section_name):
        try:
            xpath = f'//h3[contains(text(),"{section_name}")]'
            element = self.driver.find_element(By.XPATH, xpath)
        except (selenium_exceptions.NoSuchElementException, selenium_exceptions.TimeoutException):
            print(f"[INFO] Skipping section {section_name} because it doesn't exist")
            return False
        else:
            return bool(element)

    def add_languages(self, instructions):
        # CHECK IF LANGUAGES SECTION EXIST
        if not self.check_section_exist("Languages"):
            return instructions
        if len(self.load_languages()):
            # click ADD button
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Languages")]'
                                 '/following::button[contains(text(),"Add")][1]'])
            )
            # fill Languages
            languages_count = len(self.load_languages())
            for idx, language in enumerate(self.load_languages(), start=1):
                # Fluent ?
                if language["fluent"]:
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Languages {idx}")]'
                                         f'/following::text()[contains(.,"I am fluent in this language")]'
                                         f'/following::input[1]']))
                instructions += [
                    # Language
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'//text()[contains(.,"Languages {idx}")]'
                                     f'/following::text()[contains(.,"Language")]'
                                     f'/following::button[1]',
                                     language["language"]],
                             options={"value_is_pattern": True}),
                    # Reading
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Reading Proficiency")]'
                                     f'/following::button[1]',
                                     language["comprehension"]],
                             options={"value_is_pattern": True}),
                    # Speaking
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Speaking Proficiency")]'
                                     f'/following::button[1]',
                                     language["overall"]],
                             options={"value_is_pattern": True}),
                    # Translation
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Translation")]'
                                     f'/following::button[1]',
                                     language["reading"]],
                             options={"value_is_pattern": True}),
                    # Writing
                    PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                             params=[f'/following::text()[contains(.,"Writing Proficiency")]'
                                     f'/following::button[1]',
                                     language["writing"]],
                             options={"value_is_pattern": True}),
                ]

                # check if more languages remaining
                if not idx == languages_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[f'//text()[contains(.,"Languages {idx}")]'
                                         f'/following::button[contains(text(),"Add")][1]']),
                    )
        return instructions

    def add_websites(self, instructions):
        if not self.check_section_exist("Websites"):
            return instructions

        websites_count = len(self.resume_data["my-experience"]["websites"])
        if websites_count:
            # click ADD button
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=['//text()[contains(.,"Websites")]'
                                 '/following::button[contains(text(),"Add")]']),

            )
            # fill websites
            for idx, website in enumerate(self.resume_data["my-experience"]["websites"], start=1):
                instructions += [
                    # Website
                    PageStep(action="LOCATE_AND_CLICK",
                             params=[
                                 f'//div[@data-automation-id="websitePanelSet-{idx}"]',
                                 f'//input[@data-automation-id="website"]',
                                 website])
                ]
                # check if more languages remaining
                if not idx == websites_count:
                    # Add another
                    instructions.append(
                        PageStep(action="LOCATE_AND_CLICK",
                                 params=[
                                     '//button[@data-automation-id="Add Another"'
                                     ' and @aria-label="Add Another Websites"]'])
                    )
            # Save and continue
            instructions.append(
                PageStep(action="LOCATE_AND_CLICK",
                         params=[
                             '//button[contains(text(),"Save and Continue")]'])
            )

        return instructions

    def fill_my_experience_page(self):
        # instructions = []
        # steps = {
        #     "WORKS": self.add_works,
        #     "EDUCATION": self.add_education,
        #     "LANGUAGES": self.add_languages,
        #     "RESUME": self.add_resume,
        #     "WEBSITES": self.add_websites,
        # }
        # for step_name, action in steps.items():
        #     print(f"[INFO] adding {step_name}")
        #     instructions = action(instructions)

        # self.execute_instructions(instructions=instructions)
        from collections import deque
        instructions = deque()
        instructions = self.add_works(instructions)
        self.execute_instructions2(instructions=instructions)

        instructions = self.add_education(instructions)
        self.execute_instructions2(instructions=instructions)

        instructions = self.add_languages(instructions)
        self.execute_instructions2(instructions=instructions)

        instructions = self.add_resume(instructions)
        self.execute_instructions2(instructions=instructions)

        # instructions = self.add_websites(instructions)
        # self.execute_instructions2(instructions=instructions)


    def fill_my_additional_information(self):
        if self.check_application_review_reached():
            print("[INFO] Application completed ! click submit")
        else:
            print("[INFO] Please complete the required information and ")
        # fill the available information until it reach review page
        information = self.load_additional_information()
        instructions = [
            # 18 yo ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"Are you at least 18")]'
                             f'/following::button[1]',
                             information["above-18-year"]]),
            # high school or GED ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"Do you have a high school")]'
                             f'/following::button[1]',
                             information["high-school-diploma"]]),
            # authorized to work ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"authorized to work")]'
                             f'/following::button[1]',
                             information["work-authorization"]]),
            # visa sponsorship ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"sponsorship")]'
                             f'/following::button[1]',
                             information["visa-sponsorship"]]),
            # Serving military ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"Have you served")]'
                             f'/following::button[1]',
                             information["served-military"]]),
            # military spouse ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"former military spouse")]'
                             f'/following::button[1]',
                             information["military-spouse"]]),
            # Protected veteran
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"Protected Veteran")]'
                             f'/following::button[1]',
                             information["protected-veteran"]]),
            # ethnicity
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"ethnicity category")]'
                             f'/following::button[1]',
                             information["ethnicity"]]),
            # Gender / self identification
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//text()[contains(.,"Gender")]'
                             f'/following::button[1]',
                             information["self-identification"]]),

            # Accept Terms ?
            PageStep(action="LOCATE_DROPDOWN_AND_FILL"
                     , params=[f'//text()[contains(.,"I have read and consent")]'
                               f'/following::input[1]',
                               information["accept-terms"]]),
            ## SELF Identify
            # Language
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//h2[contains(text(),"Self Identify")]'
                             f'/following::text()[contains(.,"Language")]'
                             f'/following::button[1]',
                             information["language"]]),
            # Name
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//h2[contains(text(),"Self Identify")]'
                             f'/following::text()[contains(.,"Name")]'
                             f'/following::input[1]',
                             self.resume_data["my-information"]["first-name"] +
                             " " +
                             self.resume_data["my-information"]["last-name"]
                             ]),
            # Today's Date
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//h2[contains(text(),"Self Identify")]'
                             f'/following::text()[contains(.,"Date")]'
                             f'/following::input[1]',
                             today_date_in_keys()]),

            # Disability
            PageStep(action="LOCATE_DROPDOWN_AND_FILL",
                     params=[f'//h2[contains(text(),"Self Identify")]'
                             f'/following::label[contains(text(),"No")]'
                             f'/preceding::input[1]',
                             information["disability"]]),
        ]

        self.execute_instructions(instructions=instructions)

    def check_application_review_reached(self):
        try:
            xpath = '//h2[contains(text(),"Review")]'
            element = self.driver.find_element(By.XPATH, xpath)
        except selenium_exceptions.NoSuchElementException:
            return False
        else:
            return bool(element)

    def check_errors_in_page(self):
        try:
            xpath = '//div[contains(text(),"Error")]'
            element = self.driver.find_element(By.XPATH, xpath)
        except selenium_exceptions.NoSuchElementException:
            return False
        else:
            return bool(element)

    def start_application(self):
        print(self.driver)
        self.driver.get(self.application_link)

        application_steps = [
            self.login,
            self.fill_my_information_page,
            self.fill_my_experience_page,
            self.fill_my_additional_information,
        ]
        steps_count = len(application_steps)
        for idx, step in enumerate(application_steps):
            step()
            if idx != steps_count - 1:
                # waiting time for page switch
                self.driver.implicitly_wait(3.0)

    # exit
    # self.driver.quit()


if __name__ == '__main__':
    APPLICATION_LINK = "https://capitalone.wd1.myworkdayjobs.com/en-US/Capital_One/login?redirect=%2Fen-US%2FCapital_One%2Fjob%2FMcLean%252C-VA%2FLead-Software-Engineer--Android_R185952-1%2Fapply%2FapplyManually"
    # APPLICATION_LINK = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/login?redirect=%2Fen-US%2FNVIDIAExternalCareerSite%2Fjob%2FUS%252C-CA%252C-Santa-Clara%2FASIC-Design-Engineer--System-ASIC_JR1976742%2Fapply%2FapplyManually"
    # APPLICATION_LINK = "https://usaa.wd1.myworkdayjobs.com/en-US/USAAJOBSWD/job/San-Antonio-Home-Office-I/Cyber-Security-Intern_R0092844/apply/applyManually"
    RESUME_PATH = "resume.yml"
    s = WorkdayAutofill(
        application_link=APPLICATION_LINK,
        resume_path=RESUME_PATH
    )
    s.start_application()
    print("hello")
