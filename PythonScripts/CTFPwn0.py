#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import re
import os

class CTFPwn:
    def __init__(self, IP, OutPuts, dirlist, speed):
        self.IP = IP
        self.OutPuts = OutPuts
        self.dirlist = dirlist
        self.speed = int(speed)
        self.rate = '--min-rate 5000' 
        self.Tspeed = '-T4' 
        
        if self.speed == 0:
            self.rate = '--max-rate 60'
            self.Tspeed = '-T2'
            
    def run_command(self, command, output_file):
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            error = result.stderr
        except subprocess.CalledProcessError as e:
            output = e.output
            error = e.stderr
        
        print("Command output:")
        print(output)
        
        with open(output_file, "w") as file:
            file.write(output)
        
        if error:
            print("Command error:")
            print(error)
        
        return output
    
    def run_rustscan(self):
        RUSTcommand = f"sudo rustscan -r 0-65535 {self.IP}"
        output_file = "RUST.txt"
        return self.run_command(RUSTcommand, output_file)
    
    def run_nmap(self):
        directory_path = f"{self.OutPuts}/Nmap"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"Directory '{directory_path}' created successfully.")
        else:
            print(f"Directory '{directory_path}' already exists.")
        
        # Read the output from the file
        with open("RUST.txt", "r") as file:
            output = file.read()

        # Use regular expression to find open ports
        open_ports = re.findall(r'Open \S+:(\d+)', output)

        # Print and store the open ports
        print("Open Ports:", open_ports)

        # If you want to store them in a variable, you can use a list
        open_ports_list = list(map(int, open_ports))
        print("Open Ports as integers:", open_ports_list)
        
        #Nmap port scan for Rust check  along with Nmap -A scan  & vuln scan
        command = f"sudo nmap -p- {self.rate} {self.Tspeed} -vvv {self.IP} -oA {self.OutPuts}/Nmap/ports"
        output_file = f"{self.OutPuts}/Nmap/ports.nmap"

        command1 = "sudo nmap -A -p"+",".join(map(str, open_ports_list))+f" {self.rate} {self.Tspeed} -vvv {self.IP} -oA {self.OutPuts}/Nmap/mapped"
        output_file1 = f"{self.OutPuts}/Nmap/mapped.nmap"
        
        command2 = "sudo nmap --script=vuln -p"+",".join(map(str, open_ports_list))+f" {self.rate} {self.Tspeed} -vvv {self.IP} -oA Nmap/vuln"
        output_file2 = f"{self.OutPuts}/Nmap/vuln.nmap"


        # Run the first command
        self.run_command(command, output_file)

        # Run the second command
        self.run_command(command1, output_file1)
        
        # Run the thrid command
        self.run_command(command2, output_file2)

    def run_sploit(self):
        command = "sudo searchsploit --nmap -v Nmap/mapped.xml | sudo tee SSploite.txt"
        output_file = f"{self.OutPuts}/SSploite.txt"
        self.run_command(command, output_file)

    def run_ferox(self):
        #scan Nmap/mapped file for http or https methods and save there ports
        # Read the output from the file
        output_file_path = f"{OutPuts}/Nmap/mapped.nmap"
        with open(output_file_path, "r") as file:
            output = file.read()

        # Regular expression pattern to find ports with HTTP or HTTPS methods
        pattern = r'(\d+)(?=\/tcp\s+open\s+http)'

        # Finding matches using regex
        matches = re.findall(pattern, output, re.IGNORECASE | re.DOTALL)

        # Printing the list of ports with HTTP methods
        print("Ports with HTTP methods:")
        print(matches)

        formatted_list = [f"{IP}:{port}" for port in matches]

        # Printing the new formatted list
        print("Formatted IP:Port list:")
        print(formatted_list)

        for url in formatted_list:
            command = f"sudo feroxbuster -u http://{url}/ --wordlist {self.dirlist} -o statusferox{url}.txt"
            output_file = f"{self.OutPuts}/statusferox{url}.txt"
            try:
                # Execute the command using subprocess
                self.run_command(command, output_file)
            except subprocess.CalledProcessError as e:
                print(f"Command '{command}' failed with error: {e}")


        for url in formatted_list:
            command = f"sudo feroxbuster -u http://{url}/ --wordlist {self.dirlist} -C 500 -o statferox{url}.txt"
            command1 = f"sudo feroxbuster --silent -u http://{url}/ --wordlist {self.dirlist} -C 500 -o ferox{url}.txt"
            output_file = f"{self.OutPuts}/statferox{url}.txt"
            output_file1 = f"{self.OutPuts}/ferox{url}.txt"
            try:
                # Execute the command using subprocess
                print(f"scanning http://{url}/ or directory output {self.OutPuts}/statferox{url}.txt")
                self.run_command(command, output_file)
                print(f"scanning http://{url}/ or directory output {self.OutPuts}/ferox{url}.txt")
                self.run_command(command1, output_file1)
            except subprocess.CalledProcessError as e:
                print(f"Command '{command}' failed with error: {e}")
        
        
    # Implement other methods as per your original code

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 script_name.py <arg1> <arg2> <arg3> <arg4> ")
        print("Example:")
        print("sudo python3 ~/tools/PythonScripts/CTFPwn.py 10.10.11.239 ~/current/working/directory ~/directoy/wordlist 1 (A faster scan for CTF's)")
        print("sudo python3 ~/tools/PythonScripts/CTFPwn.py 10.10.11.239 ~/current/working/directory ~/direcoty/wordlist 0 (A slower scan for real-world stealth)")
        # ... rest of your usage instructions
        sys.exit(1)

    IP, OutPuts, dirlist, speed = sys.argv[1:5]
    
    ctf_pwn = CTFPwn(IP, OutPuts, dirlist, speed)
    ctf_pwn.run_rustscan()
    ctf_pwn.run_nmap()
    ctf_pwn.run_sploit()
    ctf_pwn.run_ferox()
    # Call other methods in a similar way
