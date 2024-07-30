#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 18:56:47 2024

@author: blanco
"""

import os
import sys
import re
import json
import asyncio
import aiofiles
import requests
import random
import curses
import time

# Function to make HTTP requests and fetch content
def fetch_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to extract all URLs from the content and check for query parameters within the specified scope
def extract_api_calls(content, scope):
    api_calls = set()
    # Use regex to find all URLs
    pattern = re.compile(r'https?://[^\s\'"<>]+')
    matches = pattern.findall(content)
    for match in matches:
        # Check if the URL is within the specified scope and has query parameters
        if isinstance(scope, str) and scope in match and '?' in match:
            api_calls.add(match)
    return api_calls

# Function to read URLs from a file
def read_urls_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]
        return urls
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return []

# Run a shell command asynchronously with optional verbose output and queue
async def run_command(command, timeout=6000, verbose=False, output_queue=None, log_file=None):
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        if verbose:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                if output_queue:
                    await output_queue.put(f"scanning... {command}: {line.decode().strip()}")
                if log_file:
                    async with aiofiles.open(log_file, 'a') as f:
                        await f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {line.decode().strip()}\n")
                await asyncio.sleep(5)  # Adding delay to show progress for at least 5 seconds
        else:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if log_file:
                async with aiofiles.open(log_file, 'a') as f:
                    await f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {stdout.decode().strip()}\n")
            return stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        message = f"scanning... {command}: Command timed out."
        if output_queue:
            await output_queue.put(message)
        if log_file:
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        return "", "Command timed out."
    except Exception as e:
        message = f"scanning... {command}: {str(e)}"
        if output_queue:
            await output_queue.put(message)
        if log_file:
            async with aiofiles.open(log_file, 'a') as f:
                await f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        return "", str(e)

# Create a directory asynchronously if it doesn't exist
async def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' created successfully.")
    else:
        print(f"Directory '{path}' already exists.")

# Read a file asynchronously
async def read_file(file_path):
    async with aiofiles.open(file_path, 'r') as file:
        return await file.read()

# Write content to a file asynchronously
async def write_file(file_path, content, append=False):
    mode = 'a' if append else 'w'
    async with aiofiles.open(file_path, mode) as file:
        await file.write(content + '\n')

# Extract details from command output using regular expressions
def extract_details(output):
    patterns = {
        'open_ports': re.compile(r'(\d+)/tcp\s+open'),
        'http_ports': re.compile(r'(\d+)/tcp\s+open\s+http'),
        'https_ports': re.compile(r'(\d+)/tcp\s+open\s+https'),
        'domain': re.compile(r'Nmap scan report for ([a-zA-Z0-9.-]+\.[a-zA-Z]{2,6})'), # Improved regex for domain names
        'os': re.compile(r'Service Info: OS: ([^;]+)'), # Improved regex for OS details
        'os_guess': re.compile(r'Aggressive OS guesses: ([^\n]+)'), # Regex for aggressive OS guesses
        'apache': re.compile(r'Apache'),
        'nginx': re.compile(r'nginx'),
        'sql': re.compile(r'MySQL|PostgreSQL|Microsoft SQL Server|Oracle Database')
    }

    details = {
        'open_ports': set(),
        'http_ports': set(),
        'https_ports': set(),
        'domain': None,
        'os': None,
        'services': set()
    }

    for key, pattern in patterns.items():
        matches = pattern.findall(output)
        if key == 'domain' and matches:
            details[key] = matches[0]
        elif key == 'os' and matches:
            details[key] = matches[0]
        elif key == 'os_guess' and matches:
            if details['os']:
                details['os'] += f"; {matches[0]}"
            else:
                details['os'] = matches[0]
        elif key in ['apache', 'nginx', 'sql'] and matches:
            details['services'].update(matches)
        elif matches:
            details[key].update(matches)

    # Debugging: Print extracted details
    print(f"Extracted details: {details}")

    return details

# Extract subdomains from a JSON file asynchronously
async def extract_subdomains_from_file(file_path):
    subdomains = set()
    try:
        async with aiofiles.open(file_path, 'r') as file:
            data = await file.read()
            data = json.loads(data)
            for result in data['results']:
                subdomains.add(result['host'])
    except Exception as e:
        print(f"Error reading subdomains from file: {e}")
    return list(subdomains)

# Check if a web proxy is available asynchronously
async def check_webproxy():
    command = "curl -I http://127.0.0.1:8080"
    output, error = await run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

# Check if Tor is available for a given IP asynchronously
async def check_tor(ip):
    command = f"proxychains curl http://{ip}"
    output, error = await run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

# Ensure the script is run as root
def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Please rerun with 'sudo'.")
        sys.exit(1)

# Update fingerprint file
async def update_fingerprint(fingerprint_file, details):
    async with aiofiles.open(fingerprint_file, "w") as f:
        await f.write(f"Proxys: {details['tor']}, {details['webproxy']}, {details['ffuf2burp']} \n")
        await f.write(f"Domain: {details['domain_name']}\n")
        await f.write(f"Domain to IP: {details['IP']}\n")
        await f.write(f"All Open Ports: {list(details['open_ports'])}\n")
        await f.write(f"HTTP Ports: {list(details['http_ports'])}\n")
        await f.write(f"HTTPS Ports: {list(details['https_ports'])}\n")
        await f.write(f"Targets: {details['targets_string']}\n")
        await f.write(f"OS Details: {details['os_details']}\n")
        await f.write(f"Services: {', '.join(details['services'])}\n")


# Main function that orchestrates the entire scanning process
async def main(output_queue):
    check_root()

    # Ensure correct usage
    if len(sys.argv) != 4:
        print("Usage: python3 script_name.py <arg1> <arg2> <arg3>")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py <IP> <user> <LV:0-5'1,3,5 faster scans higher number deeper enumeration'> (1 = Smaller wordlist) <speed:0|1> (0 = A faster scan 'LOUDER'")
        print("Example:")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py X.X.X.X blanco 0")
        sys.exit(1)

    IP, user, LV = sys.argv[1], sys.argv[2], int(sys.argv[3])
    
    # Set Speed, sublist and dirlist based on enumeration level
    if LV == 0:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-small.txt', '--min-rate 1000 -T2')
    elif LV == 1:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-small.txt', '--min-rate 6000 -T4')    
    elif LV == 2:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt', '--min-rate 1000 -T2')
    elif LV == 3:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt', '--min-rate 6000 -T4')
    elif LV == 4:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt', '--min-rate 1000 -T2')
    elif LV == 5:
        sublist, dirlist, speed_option = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt', '--min-rate 6000 -T4')
    else:
        raise ValueError("Invalid value for EnumLV")

    print(f"Sublist: {sublist}")
    print(f"Dirlist: {dirlist}")

       
    # Check for web proxy and Tor
    webproxy, ffuf2burp = '', '-replay-proxy http://127.0.0.1:8080' if await check_webproxy() else ''
    tor = 'proxychains' if await check_tor(IP) else ''
    print("Tor setting:", tor)

    current_working_directory = os.getcwd()
    print("Current working directory:", current_working_directory)
    outputs = current_working_directory

    log_file = os.path.join(outputs, "script_log.txt")
    
    # Create necessary directories
    prep = [
        f'sudo mkdir -p {outputs}/scan/Nmap',
        f'sudo mkdir -p {outputs}/cherry',
        f'sudo mkdir -p {outputs}/recon',
        f'sudo mkdir -p {outputs}/attacks',
        f'sudo mkdir -p {outputs}/zap',
        f'sudo chown -R {user}:{user} {outputs}/*'
    ]

    prep_tasks = [run_command(command, log_file=log_file) for command in prep]
    await asyncio.gather(*prep_tasks)

    # Define fingerprint commands
    fingerprint_commands = [
        f"{tor} ping -c 2 {IP}",
        f"{tor} sudo rustscan -t 2000 -b 2000 --ulimit 5000 -r 0-65535 -a {IP} | sudo tee rust.txt",
        f"{tor} sudo nmap -p- {speed_option} {webproxy} -vvv {IP} -oA {outputs}/scan/Nmap/ports",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv -sn {IP} -oA {outputs}/scan/Nmap/host",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv -O {IP} -oA {outputs}/scan/Nmap/OS",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv -sC {IP} -oA {outputs}/scan/Nmap/script",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv -sV {IP} -oA {outputs}/scan/Nmap/version",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv --traceroute {IP} -oA {outputs}/scan/Nmap/trace",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv --script=vuln {IP} -oA {outputs}/scan/Nmap/vuln"
    ]


    details = {
        'tor': tor,
        'webproxy': webproxy,
        'ffuf2burp': ffuf2burp,
        'IP': IP,
        'open_ports': set(),
        'http_ports': set(),
        'https_ports': set(),
        'domain_name': None,
        'os_details': None,
        'services': set(),
        'targets_string': ""
    }

    # Execute fingerprint commands
    fingerprint_tasks = [run_command(command, output_queue=output_queue, log_file=log_file) for command in fingerprint_commands]
    results = await asyncio.gather(*fingerprint_tasks)

    for output, error in results:
        if error:
            await output_queue.put(f"Error: {error}")
            continue
        await output_queue.put(f"Output: {output}")
        scan_details = extract_details(output)
        print(f"Extracted scan details: {scan_details}")  # Debug statement
        details['open_ports'].update(scan_details['open_ports'])
        details['http_ports'].update(scan_details['http_ports'])
        details['https_ports'].update(scan_details['https_ports'])
        if scan_details['domain']:
            details['domain_name'] = scan_details['domain']
        if scan_details['os']:
            details['os_details'] = scan_details['os']
        details['services'].update(scan_details['services'])

        targets = [f"{IP}:{port}" for port in details['http_ports'] | details['https_ports']]
        details['targets_string'] = ", ".join(targets)

        # Update fingerprint file after each scan
        fingerprint_file = os.path.join(outputs, "fingerprint.txt")
        await update_fingerprint(fingerprint_file, details)

    # Subdomain enumeration and directory enumeration for each found subdomain
    EnumSub = f'{outputs}/recon/SubFfuf.txt'
    SubLog = f'{outputs}/recon/ffufsub.log'
    subdomain_enum_command = f'{tor} sudo ffuf -w {sublist} -u http://{details["domain_name"]}/ -H "Host: FUZZ.{details["domain_name"]}" {ffuf2burp} -fw 9  -o {EnumSub} > {SubLog} 2>&1'
    await run_command(subdomain_enum_command, output_queue=output_queue, log_file=log_file)
    
    # Initialize sets for subdomains, directories, and discovered API calls
    discovered_urls = set()
    subdomains = await extract_subdomains_from_file(EnumSub)
    discovered_urls.update(subdomains)
    enum_logs = [SubLog]

    # Create a URL queue for processing URLs
    url_queue = asyncio.Queue()
    for url in discovered_urls:
        await url_queue.put(url)

    # Process subdomains and directories
    while not url_queue.empty():
        dir_enum_tasks = []
        for subdomain in subdomains:
            EnumDir = f'{outputs}/recon/{subdomain}dir.txt'
            DirLog = f'{outputs}/recon/URLs.log'
            dir_enum_command = f'{tor} feroxbuster --url http://{subdomain} --silent -o {EnumDir} >> {DirLog} 2>&1'
            dir_enum_tasks.extend([run_command(dir_enum_command, output_queue=output_queue, log_file=log_file)])
            # Check if the directory log file exists before trying to read it
            urls = read_urls_from_file(DirLog)

            for url in urls:
                content = fetch_content(url)
                if content:
                    api_calls = extract_api_calls(content, f'http://{subdomain}')
                    for api_call in api_calls:
                        api_file = os.path.join(outputs, f"{outputs}/attacks/Injectpoints.txt")
                        await write_file(api_file, api_call, append=True)
                        injects = f"{outputs}/attacks/Injectpoints.txt"
                        inject_urls = read_urls_from_file(injects)
                        
                        # Create a injection point list
                        inject_queue = asyncio.Queue()
                        for url in inject_urls:
                            await inject_queue.put(url)
                            
                        # Attack injection points
                        while not inject_queue.empty():
                            
                            inject_tasks = []
                            for AttackPoint in inject_urls:
                                inject_command = f'sqlmap -u {AttackPoint} --batch --dbs > {outputs}/attacks/sqlmap_output.log 2>&1'
                                inject_tasks.extend([run_command(inject_command, output_queue=output_queue, log_file=log_file)])
            
            

        # Run directory enumeration tasks concurrently
        await asyncio.gather(*dir_enum_tasks)

    # Save discovered URLs and directories to files
    async with aiofiles.open("enum_logs.txt", "w") as file:
        for log in enum_logs:
            await file.write(f"{log}\n")

    # Create ThankYou.txt and exit
    async with aiofiles.open("ThankYou.txt", "w") as file:
        await file.write("Thank you for using WarMachine by Blanco\n")

# Display output using curses
async def display_output(stdscr, output_queue, fingerprint_file):
    WIDTH = 20
    HEIGHT = 10
    SNAKE_CHAR = 'O'
    FOOD_CHAR = '1'
    EMPTY_CHAR = ' '

    UP = 'w'
    DOWN = 's'
    LEFT = 'a'
    RIGHT = 'd'

    DIRECTION_VECTORS = {
        UP: (-1, 0),
        DOWN: (1, 0),
        LEFT: (0, -1),
        RIGHT: (0, 1)
    }

    class SnakeGame:
        def __init__(self, snake_win, info_win, fingerprint_file, output_queue):
            self.snake_win = snake_win
            self.info_win = info_win
            self.fingerprint_file = fingerprint_file
            self.output_queue = output_queue
            self.initialize_game()

        def initialize_game(self):
            self.board = [[EMPTY_CHAR] * WIDTH for _ in range(HEIGHT)]
            self.snake = [(HEIGHT // 2, WIDTH // 2)]
            self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
            self.food = self.place_food()
            self.board[self.snake[0][0]][self.snake[0][1]] = SNAKE_CHAR
            self.game_over = False
            self.snake_color = random.randint(1, 7)
            self.snake_win.attron(curses.color_pair(self.snake_color))

        def place_food(self):
            while True:
                food_position = (random.randint(0, HEIGHT - 1), random.randint(0, WIDTH - 1))
                if food_position not in self.snake:
                    self.board[food_position[0]][food_position[1]] = FOOD_CHAR
                    return food_position

        def change_direction(self):
            head_y, head_x = self.snake[0]
            food_y, food_x = self.food

            if head_y < food_y:
                new_direction = DOWN
            elif head_y > food_y:
                new_direction = UP
            elif head_x < food_x:
                new_direction = RIGHT
            elif head_x > food_x:
                new_direction = LEFT
            else:
                new_direction = self.direction

            dy, dx = DIRECTION_VECTORS[new_direction]
            new_head = (head_y + dy, head_x + dx)
            if new_head in self.snake:
                new_direction = self.direction

            self.direction = new_direction

        def move_snake(self):
            head_y, head_x = self.snake[0]
            dy, dx = DIRECTION_VECTORS[self.direction]
            new_head = (head_y + dy, head_x + dx)

            if (0 <= new_head[0] < HEIGHT) and (0 <= new_head[1] < WIDTH) and (new_head not in self.snake):
                self.snake.insert(0, new_head)
                if new_head == self.food:
                    self.food = self.place_food()
                else:
                    tail = self.snake.pop()
                    self.board[tail[0]][tail[1]] = EMPTY_CHAR
                self.board[new_head[0]][new_head[1]] = SNAKE_CHAR
            else:
                self.game_over = True

        def display(self):
            self.snake_win.clear()
            for row in self.board:
                self.snake_win.addstr(''.join(row) + '\n')
            self.snake_win.addstr(f'Score: {len(self.snake) - 1}\n')
            self.snake_win.refresh()

        async def play(self):
            while True:
                self.initialize_game()
                while not self.game_over:
                    self.display()
                    self.change_direction()
                    self.move_snake()
                    await self.update_info_win()
                    await asyncio.sleep(0.2)
                self.display()
                try:
                    self.snake_win.addstr('Game Over!\n')
                    self.snake_win.refresh()
                    await asyncio.sleep(2)
                except curses.error:
                    pass

        async def update_info_win(self):
            self.info_win.clear()
            self.info_win.addstr('Scanning...\n')
            try:
                async with aiofiles.open(self.fingerprint_file, 'r') as file:
                    async for line in file:
                        self.info_win.addstr(line)
            except FileNotFoundError:
                self.info_win.addstr('Fingerprint file not found.\n')
            except curses.error:
                pass  # Ignore curses errors caused by trying to write too much text
            while not self.output_queue.empty():
                message = await self.output_queue.get()
                lines = message.split('\n')
                for line in lines:
                    try:
                        self.info_win.addstr(line[:self.info_win.getmaxyx()[1] - 1] + '\n')
                    except curses.error:
                        pass
            self.info_win.refresh()

    curses.curs_set(0)
    curses.start_color()
    for i in range(1, 8):
        curses.init_pair(i, i, curses.COLOR_BLACK)
    snake_win = curses.newwin(HEIGHT + 2, WIDTH + 2, 0, 0)
    info_win = curses.newwin(HEIGHT + 2, WIDTH * 2, 0, WIDTH + 3)
    game = SnakeGame(snake_win, info_win, fingerprint_file, output_queue)
    await game.play()

# Main program entry point
async def main_program():
    output_queue = asyncio.Queue()
    fingerprint_file = os.path.join(os.getcwd(), "fingerprint.txt")

    # Start the main task
    main_task = asyncio.create_task(main(output_queue))
    # Start the display output task within the curses environment
    curses_task = asyncio.create_task(curses.wrapper(display_output, output_queue, fingerprint_file))

    # Run both tasks concurrently
    await asyncio.gather(main_task, curses_task)

if __name__ == "__main__":
    # Use asyncio.run to start the main_program
    asyncio.run(main_program())
