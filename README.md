# PwnCrack Addons 🚀

## Why pwncrack.org? 🌐

PwnCrack.org offers a faster and more feature-rich experience for uploading and managing your handshake files. Key features include:
- ⚡ **Faster uploads** compared to other services.
- 📂 **Support for uploading hc22000 files**.
- 🗑️ **Ability to delete handshakes** and automatically remove duplicates.
- 📡 **View BSSID information**.
- 🎨 **Customizable themes**.
- 🏆 **Leaderboards for both uploaders and crackers**.
- 🔍 **A searchable password list** and more.

## help_crack.py 🔧

This script helps you configure and run Hashcat for cracking passwords. Below are the settings you need to configure:

````python
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
````

**Note:** Ensure `hashcat.exe` is in the same folder as the Python file on Windows, or Hashcat is usable as a command in that directory for every OS.

## pwnagotchi plugin pwncrack.py 🤖

This plugin auto-uploads handshakes to pwncrack.org and is significantly faster at uploading than wpa-sec because it combines them before uploading to save time. Below is the configuration:

````python
- `main.plugins.pwncrack.enabled = true`
- `main.plugins.pwncrack.key = ""`
- `main.plugins.pwncrack.handshakes_dir = "/home/pi/handshakes"`
- `main.plugins.pwncrack.whitelist = ["your-SSID1", "your-SSID2"]`
````

## AOupload.py 📤

This script uploads all `*.hc22000` files in the directory for users of tools like AngryOxide and similar tools. If your hash files don't end in `*.hc22000`, you can change that in line 10.

## uploadconvert.py 🔄

This script converts all `.pcap` files in the directory it's executed in and uploads them directly.
