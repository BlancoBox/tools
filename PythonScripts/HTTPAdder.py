# -*- coding: utf-8 -*-
import sys

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

# Split the content into a list of URLs, assuming one URL per line
urls = content.splitlines()

fixed_urls = fix_urls(urls)

for url in fixed_urls:
    print(url)
