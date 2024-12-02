from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium.webdriver.firefox.options import Options
import time


# Setup Selenium WebDriver (using Firefox in headless mode with optimizations)
GECKODRIVER_PATH = '/home/blanco/Downloads/geckodriver'
options = Options()
options.headless = True  # Run in headless mode for better performance
options.set_preference("permissions.default.image", 2)  # Disable image loading to speed up page loads
# JavaScript enabled for interaction purposes
options.set_preference("javascript.enabled", True)
options.set_preference("webdriver.load.strategy", "eager")  # Load only essential page elements to save time

# Initialize the WebDriver with the given options
service = FirefoxService(GECKODRIVER_PATH)
# Initialize the WebDriver
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)  # Set up an explicit wait with a 10-second timeout

# Configuration
LINKEDIN_USERNAME = "jahlove609@gmail.com"  # LinkedIn username (email address)
LINKEDIN_PASSWORD = "JA2@love$1"  # LinkedIn password
JOB_KEYWORDS = "Software Developer"  # Job title or keywords for search
JOB_LOCATION = "Remote"  # Job location for search


try:
    # Step 1: Log in to LinkedIn
    print("Navigating to LinkedIn login page...")
    driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")  # Navigate to LinkedIn login page

    print("Waiting for username input field...")
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))  # Wait until the username field is present
    username_input.send_keys(LINKEDIN_USERNAME)  # Enter the username

    print("Entering password...")
    password_input = driver.find_element(By.ID, "password")  # Locate the password field
    password_input.send_keys(LINKEDIN_PASSWORD)  # Enter the password
    password_input.send_keys(Keys.RETURN)  # Press Enter to log in
    print("Logged in successfully.")

    # Step 2: Navigate to Jobs Section
    print("Navigating to Jobs section...")
    wait.until(EC.presence_of_element_located((By.ID, "jobs-tab-icon"))).click()  # Wait for and click on the Jobs tab
    print("Jobs section opened.")

    # Step 3: Search for Jobs
    print(f"Searching for jobs with keywords: {JOB_KEYWORDS} and location: {JOB_LOCATION}...")
    search_keywords = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Search jobs']")))  # Wait until the job search input field is present
    search_keywords.clear()  # Clear any pre-existing text in the job search input field
    search_keywords.send_keys(JOB_KEYWORDS)  # Enter the job keywords

    search_location = driver.find_element(By.XPATH, "//input[@aria-label='Search location']")  # Locate the location input field
    search_location.clear()  # Clear any pre-existing text in the location input field
    search_location.send_keys(JOB_LOCATION)  # Enter the job location
    search_location.send_keys(Keys.RETURN)  # Press Enter to execute the job search
    print("Job search initiated.")

    time.sleep(3)  # Let the job search results load for 3 seconds
    print("Job search results loaded.")

    # Step 4: Automate Application Process
    job_listings = driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")  # Find all job listings in the results
    print(f"Found {len(job_listings)} job listings.")
    for listing in job_listings:
        try:
            print("Clicking on job listing...")
            listing.click()  # Click on the job listing to view details
            time.sleep(2)  # Let the job details load for 2 seconds

            print("Waiting for 'Apply' button...")
            apply_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-s-apply button")))  # Wait for the 'Apply' button to be present
            apply_button.click()  # Click on the 'Apply' button
            print("'Apply' button clicked.")

            # Fill in application fields if prompted
            # Example: Phone Number Field
            print("Waiting for phone number field...")
            phone_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone number']")))  # Wait for the phone number field to be present
            phone_field.clear()  # Clear any pre-existing text in the phone number field
            phone_field.send_keys("1234567890")  # Enter the phone number
            print("Phone number entered.")

            # Manual Step: User must review the form before clicking submit
            input("Review the form and press Enter to continue...")  # Pause for manual review of the application form
            print("Application submitted.")

        except Exception as e:
            # Handle exceptions that occur during the application process
            print(f"Skipping job listing due to error: {e}")  # Print the error message and skip to the next listing
            continue

finally:
    # Clean up
    print("Closing the browser...")
    driver.quit()  # Quit the WebDriver to close the browser and clean up resources
    print("Browser closed.")
