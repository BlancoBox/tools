# -*- coding: utf-8 -*-
import sys
import httpx

def read_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    return content

def fix_urls(urls):
    fixed_urls = []
    for url in urls:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url  # You can change this to https:// if you prefer
        fixed_urls.append(url)
    return fixed_urls

if len(sys.argv) > 1:
    file_path = sys.argv[1]
    print(f"The file path is: {file_path}")
else:
    print("No file path provided.")
    sys.exit(1)

content = read_file(file_path)

def send_request(url):
    try:
        response = httpx.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        return f"Error: {e}"

if __name__ == "__main__":
    file_path = sys.argv[1]  # Replace with the actual file path
    content = read_file(file_path)

    # Split the content into a list of URLs, assuming one URL per line
    urls = content.splitlines()

    for url in urls:
        response_text = send_request(url)
        print(f"URL: {url}\nResponse: {response_text}\n")