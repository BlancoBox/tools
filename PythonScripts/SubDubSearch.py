#!/usr/bin/env python3
# -*- coding: utf-8 -*-


 
import sys 
import subprocess



IP = sys.argv[1]
WL = sys.argv[2]
OutPuts = sys.argv[3]


dirdomains = f"sudo ffuf -u http://{IP}/FUZZ -w {WL}  -recursion -recursion-depth 3 -e html,php,index  -c  -o commondir2.txt"
# Run the command and capture the output
try:
    result = subprocess.run(dirdomains, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout
    error = result.stderr
except subprocess.CalledProcessError as e:
    output = e.output
    error = e.stderr


output_file_path = f"{OutPuts}/commondir2.txt"

# Read the output from the file
with open(output_file_path, "r") as file:
    output = file.read()
print(output)
    



