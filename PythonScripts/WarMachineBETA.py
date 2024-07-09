#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import json

def run_command(command, timeout=600):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "Command timed out."
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' created successfully.")
    else:
        print(f"Directory '{path}' already exists.")

def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

def extract_ports_and_domain(output, patterns):
    open_ports = set()
    http_ports = set()
    https_ports = set()
    domain_name = None
    for pattern, port_type in patterns:
        matches = re.findall(pattern, output, re.IGNORECASE | re.DOTALL)
        if port_type == 'http':
            http_ports.update(matches)
        elif port_type == 'https':
            https_ports.update(matches)
        elif port_type == 'domain':
            if matches:
                domain_name = matches[0]
        else:
            open_ports.update(matches)
    return list(open_ports), list(http_ports), list(https_ports), domain_name

def extract_subdomains_from_file(file_path):
    subdomains = set()
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            for result in data['results']:
                subdomains.add(result['host'])
    except Exception as e:
        print(f"Error reading subdomains from file: {e}")
    return list(subdomains)

def check_webproxy():
    command = "curl -I http://127.0.0.1:8080"
    output, error = run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

def check_tor(ip):
    command = f"proxychains curl -I http://{ip}"
    output, error = run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Please rerun with 'sudo'.")
        sys.exit(1)

def main():
    check_root()

    if len(sys.argv) != 5:
        print("Usage: python3 script_name.py <arg1> <arg2> <arg3> <arg4>")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py <IP> <user> <EnumLV:0|1|2> (1 = Smaller wordlist) <speed:0|1> (0 = A faster scan 'LOUDER'")
        print("Example:")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py X.X.X.X blanco 0 0")
        sys.exit(1)

    IP, user, EnumLV, speed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    
    if EnumLV == 0:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-small.txt')
    elif EnumLV == 1:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt')
    elif EnumLV == 2:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt')
    else:
        raise ValueError("Invalid value for EnumLV")

    print(f"Sublist: {sublist}")
    print(f"Dirlist: {dirlist}")

    rate, Tspeed = ('--min-rate 3000', '-T4') if speed == 0 else ('--max-rate 1000', '-T2')
    webproxy, ffufwebpoxy = ('--proxy http://127.0.0.1:8080', '-x http://127.0.0.1:8080' ) if check_webproxy() else ''
    tor = 'proxychains' if check_tor(IP) else ''
    print("Tor setting:", tor)

    current_working_directory = os.getcwd()
    print("Current working directory:", current_working_directory)
    outputs = current_working_directory
    
    prep = [
        f'sudo mkdir {outputs}/scan',
        f'sudo mkdir {outputs}/scan/Nmap',
        f'sudo mkdir {outputs}/cherry',
        f'sudo mkdir {outputs}/recon',
        f'sudo mkdir {outputs}/attacks',
        f'sudo mkdir {outputs}/zap',
        f'sudo chown -R {user}:{user} {outputs}/*'
    ]

    for command in prep:
        output, error = run_command(command)
        if error:
            print("Prep error:", error)
            pass

    fingerprint = [
        f"{tor} ping -c 2 {IP}",
        f"{tor} sudo rustscan -t 2000 -b 2000 --ulimit 5000 -r 0-65535 -a {IP} | sudo tee rust.txt",
        f"{tor} sudo nmap -p- {rate} {Tspeed} -vvv {IP} {webproxy} -oA {outputs}/scan/Nmap/ports",
        f"{tor} sudo nmap -sL -vvv {IP} {webproxy} -oA {outputs}/scan/Nmap/DNS"
    ]
    
    patterns = [
        (r'Open \S+:(\d+)', 'open'),
        (r'(\d+)/tcp\s+open', 'open'),
        (r'(\d+)/tcp\s+open\s+http', 'http'),
        (r'(\d+)/tcp\s+open\s+https', 'https'),
        (r'Nmap scan report for ([^\s]+)', 'domain')
    ]

    all_open_ports = set()
    http_ports = set()
    https_ports = set()
    domain_name = None

    for command in fingerprint:
        print(f"Running command: {command}")
        output, error = run_command(command)
        if error:
            print(f"Fingerprinting error with command '{command}': {error}")
            pass
        else:
            print(f"Output from command '{command}': {output}")
            if "ping" in command:
                match = re.search(r'PING [^\(]+\(([^)]+)\)', output)
                if match:
                    IP = match.group(1)
                    print(f"Resolved IP from ping: {IP}")
            open_ports, http_ports_found, https_ports_found, extracted_domain = extract_ports_and_domain(output, patterns)
            all_open_ports.update(open_ports)
            http_ports.update(http_ports_found)
            https_ports.update(https_ports_found)
            if extracted_domain:
                domain_name = extracted_domain
            print(f"Open Ports from {command}:", open_ports)
    
    all_open_ports_list = list(all_open_ports)
    http_ports_list = list(http_ports)
    https_ports_list = list(https_ports)

    targets = [f"{IP}:{port}" for port in http_ports_list + https_ports_list]
    targets_string = ", ".join(targets)

    fingerprint_file = os.path.join(outputs, "fingerprint.txt")
    with open(fingerprint_file, "w") as f:
        f.write(f"Domain: {domain_name}\n")
        f.write(f"Domain to IP: {IP}\n")
        f.write(f"All Open Ports: {all_open_ports_list}\n")
        f.write(f"HTTP Ports: {http_ports_list}\n")
        f.write(f"HTTPS Ports: {https_ports_list}\n")
        f.write(f"Targets: {targets_string}\n")

    print("Domain:", domain_name)
    print("Domain to IP:", IP)
    print("All Open Ports:", all_open_ports_list)
    print("HTTP Ports:", http_ports_list)
    print("HTTPS Ports:", https_ports_list)
    print("Targets:", targets_string)
    
    SubEnum = [
        f'{tor} ping -c 2 {domain_name}',
        f'{tor} sudo ffuf -w {sublist} -u http://{domain_name}/ {ffufwebpoxy} -H "Host: FUZZ.{domain_name}" -fc 404 -fw 9 -o SubFfuf.txt > ffuf.log 2>&1'
    ]
    
    for command in SubEnum:
        print(f"Running command: {command}")
        output, error = run_command(command)
        if error:
            print(f"Enum error with command '{command}': {error}")
            pass
        else:
            print(f"Output from command '{command}': {output}")
            if "ffuf" in command:
                subdomains = extract_subdomains_from_file("SubFfuf.txt")
                subdomains_string = ", ".join(subdomains)
                print("Subdomains found:", subdomains_string)
                with open(fingerprint_file, "a") as f:
                    f.write(f"Subdomains: {subdomains_string}\n")

                for domain in subdomains:
                    DirEnum = f'{tor} sudo feroxbuster -u "http://{domain}" -E -g -d 4 -B -w {dirlist} --threads 25  {webproxy} --silent -o {domain}dir'
                    print(f"Running command: {DirEnum}")
                    output, error = run_command(DirEnum)
                    if error:
                        print(f"Enum error with command '{DirEnum}': {error}")
                        pass
                    else:
                        print(f"Output from command '{DirEnum}': {output}")

if __name__ == "__main__":
    main()


'''
import os
import subprocess
import sys
import re

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.output, e.stderr

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' created successfully.")
    else:
        print(f"Directory '{path}' already exists.")

def read_file(file_path):
    with open(file_path, "r") as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

def extract_ports(output, pattern):
    return re.findall(pattern, output, re.IGNORECASE | re.DOTALL)

def ask_for_tor():
    while True:
        tor = input("Tor Y/N: ").upper()
        if tor == 'Y':
            return '--proxy socks4://127.0.0.1:9050'
        elif tor == 'N':
            return ''
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")

def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Please rerun with 'sudo'.")
        sys.exit(1)

def main():
    check_root()

    if len(sys.argv) != 6:  # Adjusted to expect 6 arguments
        print("Usage: python3 script_name.py <arg1> <arg2> <arg3> <arg4> <arg5>")
        print("Example:")
        print("sudo python3 ~/tools/PythonScripts/CTFPwn.py 10.10.11.239 ~/current/working/directory ~/directory/wordlist <user> 0 (A faster scan for CTF's)")
        print("sudo python3 ~/tools/PythonScripts/CTFPwn.py 10.10.11.239 ~/current/working/directory ~/directory/wordlist <user> 1 (A slower scan for real-world stealth)")
        sys.exit(1)

    IP, outputs, dirlist, user, speed = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    rate, Tspeed = ('--min-rate 3000', '-T4') if speed == 0 else ('--max-rate 1000', '-T2')
    tor = ask_for_tor()
    print("Tor setting:", tor)

    # Preparation commands
    prep = [
        f'sudo mkdir {outputs}/scan',
        f'sudo mkdir {outputs}/scan/Nmap',
        f'sudo mkdir {outputs}/cherry',
        f'sudo mkdir {outputs}/recon',
        f'sudo mkdir {outputs}/attacks',
        f'sudo mkdir {outputs}/zap',
        f'sudo chown -R {user}:{user} {outputs}/*'
    ]

    for command in prep:
        output, error = run_command(command)
        if error:
            print("Prep error:", error)
            pass

    # Ping command
    fingerprint = [
        #f"ping -v -c 6 {IP}",
        f"sudo rustscan -t 2000 -b 2000 --ulimit 5000 -r 0-65535 -a {IP} | sudo tee rust.txt",
        f"sudo nmap -Pn -sV -sU -p- {rate} {Tspeed} -vvv {IP} {tor} -oA {outputs}/scan/Nmap/ports",
       # f"sudo nmap -A -p{port_list_str} {rate} {Tspeed} -vvv {IP} {tor} -oA {outputs}/scan/Nmap/mapped"
        ]
    for command in fingerprint:
        output, error = run_command(command)
        if error:
            print("Fingerprinting error:", error)
            pass

    rust_command = f"sudo rustscan -t 2000 -b 2000 --ulimit 5000 -r 0-65535 -a {IP}"
    output, error = run_command(rust_command)
    print("Command output:", output)
    if error:
        print("Command error:", error)

    output_file = "RUST.txt"
    write_file(output_file, output)
    output = read_file(output_file)
    open_ports = list(map(int, extract_ports(output, r'Open \S+:(\d+)')))
    print("Open Ports:", open_ports)

    nmap_directory = f"{outputs}/Nmap"
    create_directory(nmap_directory)

    nmap_command = f"sudo nmap -Pn -sV -sU -p- {rate} {Tspeed} -vvv {IP} {tor} -oA {nmap_directory}/ports"
    output, error = run_command(nmap_command)
    output_file_path = f"{nmap_directory}/ports.nmap"
    output = read_file(output_file_path)
    open_ports_from_open = extract_ports(output, r'(\d+)/tcp\s+open\s+\S+\s+\S+\s+\S+\s+(\s+)')
    open_ports_list = list(set(open_ports).union(int(port) for _, port in open_ports_from_open))
    print("Open Ports:", open_ports_list)

    port_list_str = ",".join(map(str, open_ports_list))
    nmap1_command = f"sudo nmap -A -p{port_list_str} {rate} {Tspeed} -vvv {IP} {tor} -oA {nmap_directory}/mapped"
    output, error = run_command(nmap1_command)
    output_file_path = f"{nmap_directory}/mapped.nmap"
    output = read_file(output_file_path)
    print(output)

    nmap2_command = f"sudo nmap --script=vuln -p{port_list_str} {rate} {Tspeed} -vvv {IP} -oA {nmap_directory}/vuln"
    output, error = run_command(nmap2_command)
    output_file_path = f"{nmap_directory}/vuln.nmap"
    output = read_file(output_file_path)
    print(output)

    ssploit_command = f"sudo searchsploit --nmap -v {nmap_directory}/mapped.xml | sudo tee {outputs}/SSploit"
    output, error = run_command(ssploit_command)
    output_file_path = f"{outputs}/SSploit"
    output = read_file(output_file_path)
    print(output)

    pattern = r'(\d+)(?=\/tcp\s+open\s+http)'
    matches = extract_ports(read_file(f"{outputs}/Nmap/mapped.nmap"), pattern)
    formatted_list = [f"{IP}:{port}" for port in matches]
    print("Ports with HTTP methods:", matches)
    print("Formatted IP:Port list:", formatted_list)

    for url in formatted_list:
        command = f"sudo feroxbuster --silent -u http://{url}/ --wordlist {dirlist} -o ferox{url.replace(':', '_')}"
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Command '{command}' failed with error: {e}")


if __name__ == "__main__":
    main()
'''