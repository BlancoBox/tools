# -*- coding: utf-8 -*-


import subprocess
import sys
import re
import os


IP = sys.argv[1]
OutPuts = sys.argv[2]

# Define the command as a list of strings

RUSTcommand = f"sudo rustscan -r 0-65535 {IP} --ulimit 5000"
output_file = "RUST.txt"

# Run the command and capture the output
try:
    result = subprocess.run(RUSTcommand, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    error = result.stderr
except subprocess.CalledProcessError as e:
    output = e.output
    error = e.stderr

# Print the output to the console
print("Command output:")
print(output)

# Write the output to a file
with open(output_file, "w") as file:
    file.write(output)

# Print any errors to the console
if error:
    print("Command error:")
    print(error)



# Read the output from the file
with open(output_file, "r") as file:
    output = file.read()

# Use regular expression to find open ports
open_ports = re.findall(r'Open \S+:(\d+)', output)

# Print and store the open ports
print("Open Ports:", open_ports)

# If you want to store them in a variable, you can use a list
open_ports_list = list(map(int, open_ports))
print("Open Ports as integers:", open_ports_list)

#Now make Nmap folder
# Specify the path for the directory
directory_path = f"{OutPuts}/Nmap"

# Check if the directory already exists
if not os.path.exists(directory_path):
    # Create the directory
    os.makedirs(directory_path)
    print(f"Directory '{directory_path}' created successfully.")
else:
    print(f"Directory '{directory_path}' already exists.")

    
NMAPcommand = f"sudo nmap -p- --min-rate 5000 -T4 -vvv {IP} -oA Nmap/ports"

# Run the command and capture the output
try:
    result = subprocess.run(NMAPcommand, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    error = result.stderr
except subprocess.CalledProcessError as e:
    output = e.output
    error = e.stderr

output_file_path = f"{OutPuts}/Nmap/ports.nmap"

# Read the output from the file
with open(output_file_path, "r") as file:
    output = file.read()

# Use regular expression to find open ports
open_ports_from_open = re.findall(r'(\d+)/tcp\s+open\s+\S+\s+\S+\s+\S+\s+(\s+)', output)

# Use regular expression to find open ports from the provided list
open_ports_from_list = re.findall(r'(\d+)/tcp\s+open\s+\S+\s+\S+\s+\S+\s+(\s+)', output)

# Create a set to store unique open ports
unique_open_ports = set(open_ports_list)

# Add ports from the first source
unique_open_ports.update((int(port) for _, port in open_ports_from_open))

# Add ports from the second source
unique_open_ports.update((int(port) for _, port in open_ports_from_list))

# Convert the set of unique open ports to a list
open_ports_list = list(unique_open_ports)

# Print and store the open ports
print("Open Ports:", open_ports_list)

#now that we got all the ports let start scaning them

output_string = ", ".join(map(str, open_ports_list))
  
print(output_string)
  
NMAP1command = "sudo nmap -A -p"+",".join(map(str, open_ports_list))+f" --min-rate 5000 -T4 -vvv {IP} -oA Nmap/mapped"

# Run the command and capture the output
try:
    result = subprocess.run(NMAP1command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    error = result.stderr
except subprocess.CalledProcessError as e:
    output = e.output
    error = e.stderr


output_file_path = f"{OutPuts}/Nmap/mapped.nmap"

# Read the output from the file
with open(output_file_path, "r") as file:
    output = file.read()
print(output)
    
NMAP2command = "sudo nmap --script=vuln -p"+",".join(map(str, open_ports_list))+f" --min-rate 5000 -T4 -vvv {IP} -oA Nmap/vuln"

# Run the command and capture the output
try:
    result = subprocess.run(NMAP2command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    error = result.stderr
except subprocess.CalledProcessError as e:
    output = e.output
    error = e.stderr

output_file_path = f"{OutPuts}/Nmap/vuln.nmap"

# Read the output from the file
with open(output_file_path, "r") as file:
    output = file.read()
print(output)
