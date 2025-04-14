import os

def convert_files(direct, whitelist):
    # for each file in directory, change extension
    for filename in os.listdir(direct):
        if filename.endswith(".22000"):
            # check if the file is in the allow-list
            with open(whitelist, 'r', encoding='utf-8') as f:
                list_lines = f.readlines()
                list_lines = [line.strip() for line in list_lines]
                if filename in list_lines:
                    print(f"Skipping {filename} as it is in the allowlistlist")
                    continue  # Skip whitelisted files

            # change the extension to .hc22000
            new_filename = filename.replace(".22000", ".hc22000")
            os.rename(os.path.join(direct, filename), os.path.join(direct, new_filename))
            print(f"Renamed {filename} to {new_filename}")

if __name__ == "__main__":
    # Configuration

    DIRECTORY_PATH = "your_directory_with_22000"
    WHITELIST_FILE = "file_with_ssid_line_seperated"
    convert_files(DIRECTORY_PATH, WHITELIST_FILE)
