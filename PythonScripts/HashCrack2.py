#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import pyfiglet

ascii_banner = pyfiglet.figlet_format("TryHackMe \n Python 4 Pentesters \n HASH CRACKER")
print(ascii_banner)

wordlist_location = str(input('Enter wordlist file location: '))
hash_input = str(input('Enter hash to be cracked: '))


with open(wordlist_location, 'r') as file:
    for line in file.readlines():
        hash_ob = hashlib.md5(line.strip().encode())
        hashed_pass = hash_ob.hexdigest()
        hash_ob1 = hashlib.sha256(line.strip().encode())
        hashed_pass1 = hash_ob1.hexdigest()
        hash_ob2 = hashlib.sha224(line.strip().encode())
        hashed_pass2 = hash_ob2.hexdigest()
        hash_ob3 = hashlib.sha1(line.strip().encode())
        hashed_pass3 = hash_ob3.hexdigest()
        hash_ob4 = hashlib.sha384(line.strip().encode())
        hashed_pass4 = hash_ob4.hexdigest()
        hash_ob5 = hashlib.sha3_256(line.strip().encode())
        hashed_pass5 = hash_ob5.hexdigest()
        hash_ob6 = hashlib.sha3_224(line.strip().encode())
        hashed_pass6 = hash_ob6.hexdigest()
        hash_ob7 = hashlib.sha512(line.strip().encode())
        hashed_pass7 = hash_ob7.hexdigest()
        hash_ob8 = hashlib.sha3_384(line.strip().encode())
        hashed_pass8 = hash_ob8.hexdigest()
        hash_ob9 = hashlib.sha3_512(line.strip().encode())
        hashed_pass9 = hash_ob9.hexdigest()
        hash_ob10 = hashlib.shake_128(line.strip().encode())
        hashed_pass10 = hash_ob10.hexdigest()
        hash_ob11 = hashlib.shake_256(line.strip().encode())
        hashed_pass11 = hash_ob11.hexdigest()
        hash_ob12 = hashlib.blake2s(line.strip().encode())
        hashed_pass12 = hash_ob12.hexdigest()
        hash_ob13 = hashlib.blake2b(line.strip().encode())
        hashed_pass13 = hash_ob13.hexdigest()
        if hashed_pass == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
        elif hashed_pass1 == hash_input:
            print('Found cleartext password! ' + line.strip())
            exit(0)
