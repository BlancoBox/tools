#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
import yara
import os


def detect_os():
    os_info = platform.uname()

    system = os_info.system
    node_name = os_info.node
    release = os_info.release
    version = os_info.version
    machine = os_info.machine

    print(f"System: {system}")
    print(f"Node Name: {node_name}")
    print(f"Release: {release}")
    print(f"Version: {version}")
    print(f"Machine: {machine}")

    # Perform additional checks or analysis here based on the OS information
    # This is where actual malware scanning logic would be implemented


def scan_directory(directory_path, rules_file):
    try:
        # Load YARA rules from the specified file
        rules = yara.compile(rules_file)

        # Walk through the specified directory and scan files
        for root, _, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                # Match the file against the loaded YARA rules
                matches = rules.match(file_path)
                if matches:
                    print(f"File '{file_path}' matches the YARA rule(s):")
                    for match in matches:
                        print(f"- Rule: {match.rule}")

    except yara.Error as e:
        print(f"YARA error: {e}")

if __name__ == "__main__":
    detect_os()
    directory_to_scan = "/path/to/scan"  # Replace with the directory you want to scan
    rules_file_path = "malware_rules.yar"  # Replace with the path to your YARA rules file
    scan_directory(directory_to_scan, rules_file_path)
    
