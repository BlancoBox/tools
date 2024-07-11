#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import json
import asyncio
import aiofiles
import random
import threading
import time
import curses

async def run_command(command, timeout=60000, verbose=False, output_queue=None):
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
                    await output_queue.put(f"scanning... {command}")
        else:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        if output_queue:
            await output_queue.put(f"scanning... {command}: Command timed out.")
        return "", "Command timed out."
    except Exception as e:
        if output_queue:
            await output_queue.put(f"scanning... {command}: {str(e)}")
        return "", str(e)

async def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Directory '{path}' created successfully.")
    else:
        print(f"Directory '{path}' already exists.")

async def read_file(file_path):
    async with aiofiles.open(file_path, 'r') as file:
        return await file.read()

async def write_file(file_path, content):
    async with aiofiles.open(file_path, 'w') as file:
        await file.write(content)

def extract_details(output):
    patterns = {
        'open_ports': re.compile(r'(\d+)/tcp\s+open'),
        'http_ports': re.compile(r'(\d+)/tcp\s+open\s+http'),
        'https_ports': re.compile(r'(\d+)/tcp\s+open\s+https'),
        'domain': re.compile(r'Nmap scan report for ([^\s]+)'),
        'os': re.compile(r'Running: ([^\n]+)'),
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
        elif key in ['apache', 'nginx', 'sql'] and matches:
            details['services'].update(matches)
        elif matches:
            details[key].update(matches)

    return details

async def extract_subdomains_from_file(file_path):
    subdomains = set()
    try:
        async with aiofiles.open(file_path, 'r') as file:
            data = json.load(file)
            for result in data['results']:
                subdomains.add(result['host'])
    except Exception as e:
        print(f"Error reading subdomains from file: {e}")
    return list(subdomains)

async def check_webproxy():
    command = "curl -I http://127.0.0.1:8080"
    output, error = await run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

async def check_tor(ip):
    command = f"proxychains curl http://{ip}"
    output, error = await run_command(command, timeout=10)
    if "Failed to connect" in error:
        return False
    return True

def check_root():
    if os.geteuid() != 0:
        print("This script must be run as root. Please rerun with 'sudo'.")
        sys.exit(1)

async def main(output_queue):
    check_root()

    if len(sys.argv) != 5:
        print("Usage: python3 script_name.py <arg1> <arg2> <arg3> <arg4>")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py <IP> <user> <EnumLV:0|1|2> (1 = Smaller wordlist) <speed:0|1> (0 = A faster scan 'LOUDER'")
        print("Example:")
        print("sudo python3 ~/tools/PythonScripts/WarMachineBETA.py X.X.X.X blanco 0 0")
        sys.exit(1)

    IP, user, EnumLV, speed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    
    if EnumLV == 0:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-small.txt')
    elif EnumLV == 1:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt')
    elif EnumLV == 2:
        sublist, dirlist = ('/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt', '/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt')
    else:
        raise ValueError("Invalid value for EnumLV")

    print(f"Sublist: {sublist}")
    print(f"Dirlist: {dirlist}")

    speed_option = ('--min-rate 3000 -T4') if speed == 0 else ('--max-rate 1000 -T2')
    webproxy = '' # '--proxy http://127.0.0.1:8080' if await check_webproxy() else ''
    tor = 'proxychains' if await check_tor(IP) else ''
    print("Tor setting:", tor)

    current_working_directory = os.getcwd()
    print("Current working directory:", current_working_directory)
    outputs = current_working_directory
    
    prep = [
        f'sudo mkdir -p {outputs}/scan/Nmap',
        f'sudo mkdir -p {outputs}/cherry',
        f'sudo mkdir -p {outputs}/recon',
        f'sudo mkdir -p {outputs}/attacks',
        f'sudo mkdir -p {outputs}/zap',
        f'sudo chown -R {user}:{user} {outputs}/*'
    ]

    prep_tasks = [run_command(command) for command in prep]
    await asyncio.gather(*prep_tasks)

    fingerprint = [
        f"{tor} ping -c 2 {IP}",
        f"{tor} sudo rustscan -t 2000 -b 2000 --ulimit 5000 -r 0-65535 -a {IP} | sudo tee rust.txt",
        f"{tor} sudo nmap -p- {speed_option} {webproxy} -vvv {IP} -oA {outputs}/scan/Nmap/ports",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv -A {IP} -oA {outputs}/scan/Nmap/full",
        f"{tor} sudo nmap {speed_option} {webproxy} -vvv --script=vuln {IP} -oA {outputs}/scan/Nmap/vuln"
    ]

    verbose_command = random.choice(fingerprint)
    print(f"Running command with verbose output: {verbose_command}")

    # Run the verbose command
    await run_command(verbose_command, verbose=True, output_queue=output_queue)

    # Run the remaining commands asynchronously
    remaining_commands = [cmd for cmd in fingerprint if cmd != verbose_command]
    fingerprint_tasks = [run_command(command, output_queue=output_queue) for command in remaining_commands]
    results = await asyncio.gather(*fingerprint_tasks)

    all_open_ports = set()
    http_ports = set()
    https_ports = set()
    domain_name = None
    os_details = None
    services = set()

    for output, error in results:
        if error:
            await output_queue.put(f"Error: {error}")
            continue
        await output_queue.put(f"Output: {output}")
        details = extract_details(output)
        all_open_ports.update(details['open_ports'])
        http_ports.update(details['http_ports'])
        https_ports.update(details['https_ports'])
        if details['domain']:
            domain_name = details['domain']
        if details['os']:
            os_details = details['os']
        services.update(details['services'])

    all_open_ports_list = list(all_open_ports)
    http_ports_list = list(http_ports)
    https_ports_list = list(https_ports)

    targets = [f"{IP}:{port}" for port in http_ports_list + https_ports_list]
    targets_string = ", ".join(targets)

    fingerprint_file = os.path.join(outputs, "fingerprint.txt")
    async with aiofiles.open(fingerprint_file, "w") as f:
        await f.write(f"Domain: {domain_name}\n")
        await f.write(f"Domain to IP: {IP}\n")
        await f.write(f"All Open Ports: {all_open_ports_list}\n")
        await f.write(f"HTTP Ports: {http_ports_list}\n")
        await f.write(f"HTTPS Ports: {https_ports_list}\n")
        await f.write(f"Targets: {targets_string}\n")
        await f.write(f"OS Details: {os_details}\n")
        await f.write(f"Services: {', '.join(services)}\n")

    print("Domain:", domain_name)
    print("Domain to IP:", IP)
    print("All Open Ports:", all_open_ports_list)
    print("HTTP Ports:", http_ports_list)
    print("HTTPS Ports:", https_ports_list)
    print("Targets:", targets_string)
    print("OS Details:", os_details)
    print("Services:", ", ".join(services))

    SubEnum = [
        f'{tor} ping -c 2 {domain_name}',
        f'{tor} sudo ffuf -w {sublist} -u http://{domain_name}/ -H "Host: FUZZ.{domain_name}" {webproxy} -fw 9  -t 125 -o SubFfuf.txt > ffufsub.log 2>&1',
        f'{tor} sudo nikto -h http://{domain_name} -o {outputs}/scan/{domain_name}nikto.txt'
    ]

    subenum_tasks = [run_command(command, output_queue=output_queue) for command in SubEnum]
    results = await asyncio.gather(*subenum_tasks)

    for output, error in results:
        if error:
            await output_queue.put(f"Error: {error}")
            continue
        await output_queue.put(f"Output: {output}")
        if "ffuf" in output:
            subdomains = await extract_subdomains_from_file("SubFfuf.txt")
            subdomains_string = ", ".join(subdomains)
            print("Subdomains found:", subdomains_string)
            async with aiofiles.open(fingerprint_file, "a") as f:
                await f.write(f"Subdomains: {subdomains_string}\n")

            directories_and_params = []

            for subdomain in subdomains:
                dir_enum_command = [
                    f'{tor} ping -c 2 {subdomain}',
                    f'{tor} sudo ffuf -w {dirlist} -u http://{subdomain}/FUZZ {webproxy} -fc 307 -recursion -o {subdomain}_dirs.txt -t 125 >> ffufdir.log 2>&1',
                    f'{tor} sudo nikto -h http://{subdomain} -o {outputs}/scan/{subdomain}nikto.txt',
                ]
                dir_enum_tasks = [run_command(cmd, output_queue=output_queue) for cmd in dir_enum_command]
                await asyncio.gather(*dir_enum_tasks)

                async with aiofiles.open("ffufdir.log", "r") as log_file:
                    async for line in log_file:
                        if "Adding a new job to the queue:" in line:
                            found_url = line.split("Adding a new job to the queue: ")[1].strip()
                            print(f"Found URL: {found_url}")
                            directories_and_params.append(found_url)

            async with aiofiles.open("directories_and_params.txt", "w") as file:
                for item in directories_and_params:
                    await file.write(f"{item}\n")

async def display_output(output_queue):
    while True:
        message = await output_queue.get()
        if message:
            sys.stdout.write(f"\r{message}")
            sys.stdout.flush()
            await asyncio.sleep(10)

def play_snake_game(stdscr, output_queue, fingerprint_file):
    WIDTH = 20
    HEIGHT = 10
    SNAKE_CHAR = 'O'
    FOOD_CHAR = '*'
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
        def __init__(self, snake_win, info_win, fingerprint_file):
            self.snake_win = snake_win
            self.info_win = info_win
            self.fingerprint_file = fingerprint_file
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

        def play(self):
            while True:
                self.initialize_game()
                while not self.game_over:
                    self.display()
                    self.change_direction()
                    self.move_snake()
                    self.update_info_win()
                    time.sleep(0.2)
                self.display()
                try:
                    self.snake_win.addstr('Game Over!\n')
                    self.snake_win.refresh()
                    time.sleep(2)
                except curses.error:
                    pass

        def update_info_win(self):
            self.info_win.clear()
            self.info_win.addstr('Scanning...\n')
            try:
                with open(self.fingerprint_file, 'r') as file:
                    for line in file:
                        self.info_win.addstr(line)
            except FileNotFoundError:
                self.info_win.addstr('Fingerprint file not found.\n')
            except curses.error:
                pass  # Ignore curses errors caused by trying to write too much text
            self.info_win.refresh()

    def run_snake_game(stdscr):
        curses.curs_set(0)
        curses.start_color()
        for i in range(1, 8):
            curses.init_pair(i, i, curses.COLOR_BLACK)
        snake_win = curses.newwin(HEIGHT + 2, WIDTH + 2, 0, 0)
        info_win = curses.newwin(HEIGHT + 2, WIDTH * 2, 0, WIDTH + 3)
        game = SnakeGame(snake_win, info_win, fingerprint_file)
        game.play()

    try:
        curses.wrapper(run_snake_game)
    except curses.error:
        pass

if __name__ == "__main__":
    output_queue = asyncio.Queue()
    main_thread = threading.Thread(target=asyncio.run, args=(main(output_queue),))
    main_thread.start()
    display_thread = threading.Thread(target=asyncio.run, args=(display_output(output_queue),))
    display_thread.start()
    fingerprint_file = os.path.join(os.getcwd(), "fingerprint.txt")
    curses.wrapper(play_snake_game, output_queue, fingerprint_file)
