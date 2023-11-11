#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import urllib.parse

def url_encode_line(line):
    return urllib.parse.quote(line)

def url_encode_file(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    encoded_lines = [url_encode_line(line.strip()) for line in lines]

    with open(output_file, 'w') as f:
        f.write('\n'.join(encoded_lines))

if __name__ == "__main__":
    input_file = input("input.txt")  # Replace with your input file
    output_file = input("output.txt")  # Replace with desired output file

    url_encode_file(input_file, output_file)
