import requests
import subprocess
import os
import sys
import time
import uuid  # Add this import

SERVER_URL = "http://pwncrack.org"
HASHCAT_BIN = "hashcat"
WORDLIST = "password.txt"  # Update this path
CRACKER_ID = str(uuid.uuid4())  # Generate a unique cracker ID

def get_work():
    try:
        response = requests.get(f"{SERVER_URL}/get_work")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting work: {e}")
        return None

def download_file(url, filename):
    try:
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def submit_results(file_name, potfile_content):
    try:
        print(f"Submitting results for {file_name}")
        response = requests.post(
            f"{SERVER_URL}/put_work",
            json={
                "file_name": file_name,
                "potfile_content": potfile_content
            }
        )
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error submitting results: {e}")
        return False

def send_hashrate(file_name, hashrate):
    try:
        response = requests.post(
            f"{SERVER_URL}/update_hashrate",
            json={
                "file_name": file_name,
                "hashrate": hashrate,
                "cracker_id": CRACKER_ID  # Send cracker_id
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending hashrate: {e}")
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
    print(f"Potfile: {file_name}.potfile")
    
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
    
    second_file_name = None
    
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
        
        # Download the second file while the first one is being processed
        files = [f for f in os.listdir('.') if f.endswith('.hc22000') and f != file_name]
        if len(files) == 1:
            second_file_name = files[0]
            print(f"Downloading second file: {second_file_name}")
            download_file(f"{SERVER_URL}/download/{second_file_name}", second_file_name)
        
        while process.poll() is None:
            time.sleep(1)
            hashrate = parse_hashrate(log_file)
            print(f"Current hash rate: {hashrate} H/s")
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
            print(f"Starting hashcat with second file: {second_file_name}")
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
        print(f"Error downloading wordlist: {e}")
        return None

def main():
    wordlist_name = "default.gz"  # Use default.txt as the wordlist file name
    wordlist_path = download_wordlist(wordlist_name)
    if wordlist_path:
        global WORDLIST
        WORDLIST = wordlist_path
    else:
        print("Failed to download wordlist")
        return

    while True:
        work = get_work()
        if not work:
            print("No work available, waiting...")
            time.sleep(60)
            continue
            
        file_name = work['file_name']
        download_url = work['download_url']
        
        print(f"Received work: {file_name}")
        
        if download_file(download_url, file_name):
            potfile_content = crack_file(file_name)
            
            if potfile_content:
                print(f"Found results for {file_name}")
                if submit_results(file_name, potfile_content):
                    print("Results submitted successfully")
                else:
                    print("Failed to submit results")
            else:
                print(f"No results found for {file_name}")
        else:
            print(f"Failed to download {file_name}")

if __name__ == "__main__":
    main()