import os
import subprocess
import requests
import socket
import logging
from pwnagotchi.plugins import Plugin
from pwnagotchi.utils import StatusFile

class UploadConvertPlugin(Plugin):
    __author__ = 'Terminatoror'
    __version__ = '0.5.0'
    __license__ = 'GPL3'
    __description__ = 'Converts .pcap files to .hc22000 and uploads them to pwncrack.org when internet is available.'

    def __init__(self):
        self.server_url = 'http://pwncrack.org/upload_handshake' #leave this as is
        self.potfile_url = 'http://pwncrack.org/download_potfile_script' #leave this as is
        self.key = 'your-key-here' #change this to your key
        self.handshake_dir = '/root/handshakes/' #cjange this to your handshake directory
        self.combined_file = os.path.join(self.handshake_dir, 'combined.hc22000')
        self.potfile_path = os.path.join(self.handshake_dir, 'hashcat.potfile')
        self.status = StatusFile('/root/.pwnagotchi-uploadconvert-plugin')

    def on_internet_available(self, agent):
        logging.info(f"Using key: {self.key}")  # Log the key being used
        self._convert_and_upload()
        self._download_potfile()

    def _convert_and_upload(self):
        # Convert all .pcap files to .hc22000
        pcap_files = [f for f in os.listdir(self.handshake_dir) if f.endswith('.pcap')]
        if pcap_files:
            for pcap_file in pcap_files:
                subprocess.run(['hcxpcapngtool', '-o', self.combined_file, os.path.join(self.handshake_dir, pcap_file)])

            # Ensure the combined file is created
            if not os.path.exists(self.combined_file):
                open(self.combined_file, 'w').close()

            # Upload the combined .hc22000 file
            with open(self.combined_file, 'rb') as file:
                files = {'handshake': file}
                data = {'key': self.key}
                response = requests.post(self.server_url, files=files, data=data)

            # Log the response
            logging.info(f"Upload response: {response.json()}")
            os.remove(self.combined_file)  # Remove the combined.hc22000 file
        else:
            logging.info("No .pcap files found to convert.")

    def _download_potfile(self):
        response = requests.get(self.potfile_url, params={'key': self.key})
        if response.status_code == 200:
            with open(self.potfile_path, 'w') as file:
                file.write(response.text)
            logging.info(f"Potfile downloaded to {self.potfile_path}")
        else:
            logging.error(f"Failed to download potfile: {response.status_code}")
            logging.error(response.json())  # Log the error message from the server
