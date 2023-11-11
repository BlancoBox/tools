#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import requests 
import sys 

WL = "/usr/share/wordlists/PythonForPentesters/wordlist2.txt"

sub_list = open(WL).read() 
subdoms = sub_list.splitlines()

for sub in subdoms:
    sub_domains = f"http://{sub}.{sys.argv[1]}" 

    try:
        requests.get(sub_domains)
    
    except requests.ConnectionError: 
        pass
    
    else:
        print("Valid domain: ",sub_domains)
        
        
sub_list = open(WL).read() 
directories = sub_list.splitlines()
        
        
for dir in directories:
    dir_enum = f"http://{sys.argv[1]}/{dir}.html" 
    r = requests.get(dir_enum)
    if r.status_code==404: 
        pass
    else:
        print("Valid directory:" ,dir_enum)
