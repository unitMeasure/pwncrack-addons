import requests
import subprocess
import os
import sys
import time
import uuid

SERVER_URL = "http://pwncrack.org"
HASHCAT_BIN = "hashcat"
CUSTOM_ATTACK_ENABLED = False  # Set to True if you want to use custom rules
CUSTOM_WORDLIST = "password.txt"  # optional but both are required (wordlist must be in the same directory)
CUSTOM_RULES = "best64.rule"  # optional but both are required (rule file must be in the same directory)
CUSTOM_MASK_ATTACK_ENABLED = False  # Set to True if you want to use hybrid dictionary + mask attack
CUSTOM_MASKDICTIONARY = "maskdict.txt"  # optional but both are required (wordlist must be in the same directory)
CUSTOM_MASK = "?d?d?d?d?d"  # optional but both are required (mask must be in hashcat format)
CRACKER_ID = str(uuid.uuid4())  # Generate a unique cracker ID
USERKEY = "YOUR-USER-KEY"  # Add this variable
DISABLE_HWMON = False  # Set to True to disable hardware monitoring

class TerminalColors:
    ORANGE = '\033[33m'
    RED = '\033[31m'
    PURPLE = '\033[35m'
    GREEN = '\033[32m'
    RESET = '\033[0m'

def log_with_timestamp(message, color=TerminalColors.RESET):
    print(f"{time.strftime('[%H:%M:%S]')} - {color}{message}{TerminalColors.RESET}")

def get_work():
    try:
        response = requests.get(f"{SERVER_URL}/get_work")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        log_with_timestamp(f"Error getting work: {e}", TerminalColors.RED)
        return None

def download_file(url, filename):
    try:
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        log_with_timestamp(f"Error downloading file: {e}", TerminalColors.RED)
        return False

def submit_results(file_name, potfile_content):
    try:
        log_with_timestamp(f"Submitting results for {file_name}", TerminalColors.GREEN)
        response = requests.post(
            f"{SERVER_URL}/put_work",
            json={
                "file_name": file_name,
                "potfile_content": potfile_content
            }
        )
        log_with_timestamp(f"Response status code: {response.status_code}", TerminalColors.GREEN)
        log_with_timestamp(f"Response content: {response.content}", TerminalColors.GREEN)
        return response.status_code == 200
    except Exception as e:
        log_with_timestamp(f"Error submitting results: {e}", TerminalColors.RED)
        return False

def send_hashrate(file_name, hashrate):
    try:
        response = requests.post(
            f"{SERVER_URL}/update_hashrate",
            json={
                "file_name": file_name,
                "hashrate": hashrate,
                "cracker_id": CRACKER_ID,  # Send cracker_id
                "user_key": USERKEY  # Send user_key
            }
        )
        return response.status_code == 200
    except Exception as e:
        log_with_timestamp(f"Error sending hashrate: {e}", TerminalColors.RED)
        return False

def parse_hashrate(output_file):
    hashrate = 0
    with open(output_file, 'r') as f:
        for line in f:
            if line.startswith('Speed.#'):
                parts = line.split(':')
                if len(parts) > 1:
                    rate_str = parts[1].strip().split(' ')[0]
                    unit = parts[1].strip().split(' ')[1] if len(parts[1].strip().split(' ')) > 1 else ''
                    try:
                        rate = float(rate_str)
                        if unit == 'kH/s':
                            rate *= 1e3
                        elif unit == 'MH/s':
                            rate *= 1e6
                        elif unit == 'GH/s':
                            rate *= 1e9
                        elif unit == 'TH/s':
                            rate *= 1e12
                        hashrate += rate
                    except ValueError:
                        continue
    return hashrate

def parse_progress(log_file):
    progress = 0
    with open(log_file, 'r') as f:
        for line in f:
            if line.startswith('Progress.........:'):
                parts = line.split('(')
                if len(parts) > 1:
                    progress_str = parts[1].strip().split('%')[0]
                    try:
                        progress = float(progress_str)
                    except ValueError:
                        continue
    return progress

def crack_file(file_name):
    output_file = f"{file_name}.potfile"
    log_file = f"{file_name}.log"
    log_with_timestamp(f"Potfile: {file_name}.potfile", TerminalColors.PURPLE)
    
    command = [
        HASHCAT_BIN,
        "-m", "22000",
        "--outfile-format", "1,2",
        "-a", "0",
        "-o", output_file,
        "--potfile-disable",
        "--restore-disable",
        file_name,
        WORDLIST
    ]
    
    if DISABLE_HWMON:
        command.append("--hwmon-disable")
    
    second_file_name = None
    
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
        
        # Download the second file while the first one is being processed
        files = [f for f in os.listdir('.') if f.endswith('.hc22000') and f != file_name]
        if len(files) == 1:
            second_file_name = files[0]
            log_with_timestamp(f"Downloading second file: {second_file_name}")
            download_file(f"{SERVER_URL}/download/{second_file_name}", second_file_name)
        
        start_time = time.time()  # Track start time for session duration
        
        while process.poll() is None:
            time.sleep(1)
            hashrate = parse_hashrate(log_file)
            if hashrate > 0:
                log_with_timestamp(f"Current hash rate: {hashrate} H/s", TerminalColors.ORANGE)
                send_hashrate(file_name, hashrate)
        
        process.wait()
        
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
            if content:
                return content
        
        # Run second command if CUSTOM_ATTACK_ENABLED
        if CUSTOM_ATTACK_ENABLED:
            log_with_timestamp(f"Running hashcat with {CUSTOM_WORDLIST} and {CUSTOM_RULES} for {file_name}")
            command = [
                HASHCAT_BIN,
                "-m", "22000",
                "--outfile-format", "1,2",
                "-a", "0",
                "-o", output_file,
                "--potfile-disable",
                "--restore-disable",
                file_name,
                CUSTOM_WORDLIST,
                "-r", CUSTOM_RULES
            ]
            if DISABLE_HWMON:
                command.append("--hwmon-disable")
            with open(log_file, 'w') as log:
                process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
            
            while process.poll() is None:
                time.sleep(1)
                hashrate = parse_hashrate(log_file)
                if hashrate > 0:
                    log_with_timestamp(f"Current hash rate: {hashrate} H/s", TerminalColors.ORANGE)
                    send_hashrate(file_name, hashrate)
            
            process.wait()
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    content = f.read()
                if content:
                    return content
        
        # Run third command if CUSTOM_MASK_ATTACK_ENABLED
        if CUSTOM_MASK_ATTACK_ENABLED:
            log_with_timestamp(f"Running hashcat with hybrid dictionary {CUSTOM_MASKDICTIONARY} and mask {CUSTOM_MASK} for {file_name}")
            command = [
                HASHCAT_BIN,
                "-m", "22000",
                "--outfile-format", "1,2",
                "-a", "6",
                "-o", output_file,
                "--potfile-disable",
                "--restore-disable",
                file_name,
                CUSTOM_MASKDICTIONARY,
                CUSTOM_MASK
            ]
            if DISABLE_HWMON:
                command.append("--hwmon-disable")
            with open(log_file, 'w') as log:
                process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
            
            while process.poll() is None:
                time.sleep(1)
                hashrate = parse_hashrate(log_file)
                if hashrate > 0:
                    log_with_timestamp(f"Current hash rate: {hashrate} H/s", TerminalColors.ORANGE)
                    send_hashrate(file_name, hashrate)
            
            process.wait()
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    content = f.read()
                return content
        
        return None
    except subprocess.CalledProcessError:
        return None
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(log_file):
            os.remove(log_file)
        
        # Start processing the second file after the first one is done
        if second_file_name:
            log_with_timestamp(f"Starting hashcat with second file: {second_file_name}")
            crack_file(second_file_name)

def download_wordlist(wordlist_name):
    url = f"{SERVER_URL}/wordlists/{wordlist_name}"
    try:
        response = requests.get(url)
        wordlist_path = os.path.join(os.getcwd(), wordlist_name)
        with open(wordlist_path, 'wb') as f:
            f.write(response.content)
        return wordlist_path
    except Exception as e:
        log_with_timestamp(f"Error downloading wordlist: {e}", TerminalColors.RED)
        return None

def main():
    wordlist_name = "default.gz"  # Use default.txt as the wordlist file name
    wordlist_path = download_wordlist(wordlist_name)
    if wordlist_path:
        global WORDLIST
        WORDLIST = wordlist_path
    else:
        log_with_timestamp("Failed to download wordlist", TerminalColors.RED)
        return

    try:
        while True:
            work = get_work()
            if not work:
                log_with_timestamp("No work available, waiting...", TerminalColors.RED)
                time.sleep(60)
                continue
                
            file_name = work['file_name']
            download_url = work['download_url']
            
            log_with_timestamp(f"Received work: {file_name}", TerminalColors.PURPLE)
            
            if download_file(download_url, file_name):
                potfile_content = crack_file(file_name)
                
                if potfile_content:
                    log_with_timestamp(f"Found results for {file_name}", TerminalColors.GREEN)
                    if submit_results(file_name, potfile_content):
                        log_with_timestamp("Results submitted successfully", TerminalColors.GREEN)
                    else:
                        log_with_timestamp("Failed to submit results", TerminalColors.RED)
                else:
                    log_with_timestamp(f"No results found for {file_name}", TerminalColors.RED)
            else:
                log_with_timestamp(f"Failed to download {file_name}", TerminalColors.RED)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nProcess interrupted by user. Exiting gracefully.")
        print("\nThank you for using and contributing to PwnCrack!")
        sys.exit(0)

if __name__ == "__main__":
    main()
