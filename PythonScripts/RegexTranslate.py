# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import re

def translate_regex_in_file(input_file, output_file, translation_dict):
    with open(input_file, 'r') as f:
        content = f.read()

    for pattern, replacement in translation_dict.items():
        content = re.sub(pattern, replacement, content)

    with open(output_file, 'w') as f:
        f.write(content)

# Example usage:
input_file = 'input.txt'
output_file = 'output.txt'

# Define your translation dictionary, where keys are regular expressions and values are replacements
translation_dict = {
    r'pattern1': 'replacement1',
    r'pattern2': 'replacement2',
    # Add more patterns as needed
}

translate_regex_in_file(input_file, output_file, translation_dict)
