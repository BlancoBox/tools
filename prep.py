#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 03:44:48 2024

@author: blancobox
"""

import subprocess
import sys
import re
import os

if len(sys.argv) != 3:
    print("Usage: python3 script_name.py <arg1> <arg2>")
    print("Example:")
    print("sudo python3 ~/tools/PythonScripts/prep.py ~/current/working/directory user")
    sys.exit(1)

directory = sys.argv[1]
user = sys.argv[2]

#run commands
def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

def main():
    commands = [
        f'sudo mkdir {directory}/scan',
        f'sudo mkdir {directory}/cherry',
        f'sudo mkdir {directory}/recon',
        f'sudo mkdir {directory}/attacks',
        f'sudo mkdir {directory}/zap',
        f'sudo chown -R {user}:{user} {directory}/*'
            
    ]
        
    for command in commands:
        print(f"Running command: {command}")
        run_command(command)
        print("Command completed.")
        
if __name__ == "__main__":
    main()
