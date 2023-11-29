#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import re
import os



# Define the command as a list of strings
command = "burpsuite"  # Replace this with the command you want to run with sudo

# Run the command with sudo
try:
    result = subprocess.run(['sudo', '-S', *command.split()], input=b'your_sudo_password\n', text=True, capture_output=True, check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error:", e)

command = "zaproxy"  # Replace this with the command you want to run with sudo

# Run the command with sudo
try:
    result = subprocess.run(['sudo', '-S', *command.split()], input=b'your_sudo_password\n', text=True, capture_output=True, check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error:", e)

