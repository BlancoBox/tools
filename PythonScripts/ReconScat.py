#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 03:28:11 2024

@author: blancobox
"""

import subprocess
import sys
import re
import os


if len(sys.argv) != 4:
    print("Usage: python3 script_name.py <arg1> <arg2> <arg3> ")
    print("Example:")
    print("sudo python3 ~/tools/PythonScripts/ReconScat.py 10.10.11.239 ~/current/working/directory user")
    sys.exit(1)

IP = sys.argv[1]
directory = sys.argv[2]
user = sys.argv[3]
output_file = 'url.txt'

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")


def read_api_key():
    try:
        with open("/home/blancobox/apikeys/github.txt", "r") as file:
            api_key = file.read().strip()
            return api_key
    except FileNotFoundError:
        print("API key file not found.")
        return None

def extract_domains(root_domain, directory):
    # Compile regex pattern to match domain names
    domain_pattern = re.compile(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?)')

    # List to store matched domain names
    matched_domains = []

    # Iterate over files in the directory
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as file:
                # Read content of the file
                content = file.read()

                # Find all matches of domain names using regex
                domains = domain_pattern.findall(content)

                # Filter and append only domain names matching the root domain
                for domain in domains:
                    if domain.endswith(root_domain) or domain.endswith('.' + root_domain):
                        matched_domains.append(domain)

    return matched_domains

def write_to_file(domains, output_file):
    with open(output_file, 'w') as file:
        for domain in domains:
            file.write(domain + '\n')
def main():
    APYKEYGITHUB = read_api_key()

    if APYKEYGITHUB:
        commands = [
            f'gospider -d 0 -s "https://{IP}" -c 5 -t 100 -d 5 --blacklist jpg,jpeg,gif,css,tif,tiff,png,ttf,woff,woff2,ico,pdf,svg,txt | grep -Eo \'(http|https)://[^/"]+\' | anew | sudo tee gospider.txt',
            f'sudo python3 /home/blancobox/tools/github-search/github-subdomains.py -t {APYKEYGITHUB} -d {IP} | sudo tee gitsearchFOE.txt',
            f'curl -s "https://jldc.me/anubis/subdomains/{IP}" | grep -Po "((http|https):\/\/)?(([\w.-]*)\.([\w]*)\.([A-z]))\w+" | anew | sudo tee jldcFoE.txt',
            f'chaos -d {IP} | tee chaos.txt',
            f'assetfinder -subs-only {IP} -silent | grep "innogames" | sudo tee asstfin.txt',
            f"curl -s 'https://crt.sh/?q=%25.{IP}&output=json' | jq -r '.[].name_value' | assetfinder -subs-only | sed 's#$#/.git/HEAD#g' | anew | sudo tee bufferover.txt",
            f'mkdir {directory}/Amassed',
            f'amass enum -d {IP} | sudo tee amass.txt',
            f'sudo cp {directory}/amass.txt {directory}/Amassed',
            f'sudo chown -R {user}:{user} {directory}/*',
            f'cat {directory}/* >> url.txt'
    ]
        

    for command in commands:
        print(f"Running command: {command}")
        run_command(command)
        print("Command completed.")
    # Extract domain names matching the root domain
    matched_domains = extract_domains(IP, directory)

    # Write matched domain names to a new file
    write_to_file(matched_domains, output_file)

    print(f"Extracted and wrote {len(matched_domains)} domain names to {output_file}")


if __name__ == "__main__":
    main()
