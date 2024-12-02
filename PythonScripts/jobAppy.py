#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 2 1:01:01 2024

@author: blanco
"""

import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

# Setup Selenium WebDriver (using Firefox in headless mode with optimizations)
GECKODRIVER_PATH = '/home/blanco/Downloads/geckodriver'
options = Options()
options.headless = True  # Run in headless mode for better performance
options.set_preference("permissions.default.image", 2)  # Disable image loading to speed up page loads
options.set_preference("javascript.enabled", True)  # Ensure JavaScript is enabled
options.set_preference("webdriver.load.strategy", "eager")  # Load only essential page elements to save time

# Initialize the WebDriver with the given options
service = FirefoxService(GECKODRIVER_PATH)
driver = webdriver.Firefox(service=service, options=options)
wait = WebDriverWait(driver, 10)  # Set up an explicit wait with a 10-second timeout

# Configuration
LINKEDIN_USERNAME = "th1sn0tmy3ma1l@umail.com"  # LinkedIn username (email address)
LINKEDIN_PASSWORD = "Th1sCoulDB3y0urP@ssW0rd"  # LinkedIn password

# Function to introduce random human-like delay
def random_delay():
    time.sleep(random.uniform(2, 7))  # Random delay between 2 to 5 seconds

# Function to mimic user scrolling behavior
def random_mimic_user_behavior():
    scroll_chance = random.randint(1, 5)
    if scroll_chance == 1:  # Randomly scroll 20% of the time
        print("Mimicking user scrolling behavior...")
        original_position = driver.execute_script("return window.pageYOffset;")  # Record current position

        # Randomly scroll up or down by a certain amount
        scroll_distance = random.randint(300, 800)  # Random scroll distance between 300 to 800 pixels
        scroll_direction = random.choice(['up', 'down'])

        if scroll_direction == 'up':
            driver.execute_script(f"window.scrollBy(0, -{scroll_distance});")
            print(f"Scrolled up by {scroll_distance} pixels.")
        else:
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            print(f"Scrolled down by {scroll_distance} pixels.")

        time.sleep(random.uniform(1, 3))  # Pause for a moment as if reading
        print("Pausing to simulate reading...")

        # Scroll back to the original position
        driver.execute_script(f"window.scrollTo(0, {original_position});")
        print("Scrolled back to the original position.")
        random_delay()  # Add a random delay after scrolling back

try:
    # Step 1: Log in to LinkedIn
    print("Navigating to LinkedIn login page...")
    driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")  # Navigate to LinkedIn login page
    random_delay()

    print("Waiting for username input field...")
    username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))  # Wait until the username field is present
    username_input.send_keys(LINKEDIN_USERNAME)  # Enter the username
    random_delay()

    print("Entering password...")
    password_input = driver.find_element(By.ID, "password")  # Locate the password field
    password_input.send_keys(LINKEDIN_PASSWORD)  # Enter the password
    password_input.send_keys(Keys.RETURN)  # Press Enter to log in
    print("Logged in successfully.")
    random_delay()
    time.sleep(6)

    # Check for CAPTCHA by searching for the text "Let’s do a quick security check"
    if "Let’s do a quick security check" in driver.page_source:
        print("CAPTCHA detected by text. Please solve it manually.")
        random_delay()
        time.sleep(30)  # Pause for manual solving of the CAPTCHA
    else:
        print("No CAPTCHA detected.")

    while True:  # Restart the process for each job listing
        try:
            # Step 2: Navigate to Jobs Section
            print("Navigating to Jobs section...")
            driver.get("https://www.linkedin.com/jobs/")  # Navigate to the Jobs tab
            random_delay()
            time.sleep(6)
            print("Jobs section opened.")

            # Mimic user behavior randomly
            random_mimic_user_behavior()

            # Step 3: Click the "Show All" button (if exists)
            try:
                print("Attempting to locate and click the Show All button...")
                button = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'discovery-templates-jobs-home-vertical-list__footer') and @aria-label]")))
                button.click()  # Click on the button
                print("Show All button clicked successfully.")
                random_delay()
                time.sleep(6)
            except:
                print("Show All button not found, proceeding to search job cards.")

            # Step 4: Look for Easy Apply button or Job Cards on the Left Side
            try:
                # Attempt to locate the 'Easy Apply' button on the job details page
                print("Attempting to locate and click the 'Easy Apply' button on the job details page...")
                easy_apply_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//span[text()='Easy Apply']/ancestor::button"))
                )
                easy_apply_button.click()  # Click on the Easy Apply button
                print("'Easy Apply' button clicked successfully.")
                random_delay()
                time.sleep(6)
            except:
                # If the Easy Apply button is not found in the job details, try finding a job card with Easy Apply on the left side
                print("Easy Apply button not found on job details page. Looking for job card with 'Easy Apply' on the left side...")
                job_cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'job-card-container--clickable')]")
                easy_apply_found = False

                for card in job_cards:
                    try:
                        # Scroll to the card element to make it visible
                        driver.execute_script("arguments[0].scrollIntoView();", card)
                        time.sleep(1)  # Pause briefly after scrolling

                        # Check if the job card contains a span with "Easy Apply" text
                        easy_apply_span = card.find_element(By.XPATH, ".//span[contains(text(), 'Easy Apply')]")
                        if easy_apply_span:
                            print("Job card with 'Easy Apply' found. Clicking the job card...")
                            card.click()  # Click the job card to open its details
                            random_delay()
                            time.sleep(6)

                            # Now retry to click the main Easy Apply button
                            print("Attempting to locate and click the 'Easy Apply' button after selecting the job card...")
                            easy_apply_button = wait.until(
                                EC.presence_of_element_located((By.XPATH, "//span[text()='Easy Apply']/ancestor::button"))
                            )
                            easy_apply_button.click()  # Click on the Easy Apply button
                            print("'Easy Apply' button clicked successfully.")
                            random_delay()
                            time.sleep(6)
                            easy_apply_found = True
                            break
                    except Exception as e:
                        print(f"Could not click on the job card or Easy Apply button. Error: {e}")

                if not easy_apply_found:
                    print("No job cards with 'Easy Apply' were found. Skipping this job listing.")
                    continue

            # Mimic user behavior randomly
            random_mimic_user_behavior()

            # Step 5: Handle multiple "Next" buttons, "Review", and "Submit"
            while True:
                try:
                    # Fill in text input fields requiring manual entry with "3"
                    print("Attempting to locate any manual input fields for years of experience...")
                    text_inputs = driver.find_elements(By.XPATH, "//input[@type='text' and contains(@id, 'formElement')]")
                    for input_field in text_inputs:
                        if input_field.get_attribute('value') == "":
                            print(f"Entering '3' in empty input field: {input_field.get_attribute('id')}")
                            input_field.send_keys("3")
                            random_delay()

                    # Attempt to click "Next" if available
                    print("Attempting to locate and click the 'Next' button to continue to the next step...")
                    next_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Continue to next step' and contains(@class, 'artdeco-button--primary')]")))
                    next_button.click()  # Click the "Next" button to proceed to the next step
                    print("'Next' button clicked successfully.")
                    random_delay()
                    time.sleep(6)
                except:
                    # If no "Next" button, attempt to click "Review" button
                    try:
                        print("Attempting to locate and click the 'Review' button...")
                        review_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Review your application' and contains(@class, 'artdeco-button--primary')]")))
                        review_button.click()  # Click the "Review" button
                        print("'Review' button clicked successfully.")
                        random_delay()
                        time.sleep(6)

                        # Step 6: Click the "Submit application" button
                        print("Attempting to locate and click the 'Submit application' button...")
                        submit_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Submit application' and contains(@class, 'artdeco-button--primary')]")))
                        submit_button.click()  # Click the "Submit application" button
                        print("'Submit application' button clicked successfully.")
                        random_delay()
                        time.sleep(6)

                        # Break out after submission to start a new job application process
                        break

                    except Exception as e:
                        print(f"Could not find 'Review' button or 'Submit application' button. Error: {e}")
                        break

            # Print success message and restart the application for the next job listing
            print("Application submitted successfully. Moving to the next job listing.")
            time.sleep(6)

        except Exception as e:
            # Handle exceptions if the button cannot be clicked
            print(f"Error during the application process: {e}")
            continue  # Restart the job application process for the next available job listing

except Exception as e:
    # Handle exceptions that occur during the application process
    print(f"Skipping job listing due to error: {e}")  # Print the error message

finally:
    # Clean up
    print("Closing the browser...")
    driver.quit()  # Quit the WebDriver to close the browser and clean up resources
    print("Browser closed.")
