import os
import requests

# Variables
server_url = 'https://pwncrack.org/upload_handshake'
key = 'your_key_here'
combined_file = 'tmp_combined.hc22000'

# Combine all .hc22000 files into one
hc22000_files = [f for f in os.listdir('.') if f.endswith('.hc22000')]
with open(combined_file, 'wb') as outfile:
    for hc22000_file in hc22000_files:
        with open(hc22000_file, 'rb') as infile:
            outfile.write(infile.read())

# Upload the combined .hc22000 file
with open(combined_file, 'rb') as file:
    files = {'handshake': file}
    data = {'key': key}
    response = requests.post(server_url, files=files, data=data)

# Print the response
print(response.json())

# Remove the combined file after uploading
os.remove(combined_file)
