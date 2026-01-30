# This file allows you to delete ALL the files stored on your Raspberry Pi (Rpi) which contain 'UTC.txt'
# These are the logs you have created on your device, the code allows you to not have to delete
# them manually. Run it in the Thonny terminal directly - it should not be saved on your Rpi.

import os

# Get all files in the current directory
files = os.listdir()

# Find all files that contain "UTC.txt"
log_files = [f for f in files if 'UTC.txt' in f]

if log_files:
    print(f"Found {len(log_files)} log file(s) to delete:")
    for log_file in log_files:
        print(f"  - {log_file}")
        os.remove(log_file)
    print("All UTC log files deleted")
else:
    print("No UTC.txt log files found")
