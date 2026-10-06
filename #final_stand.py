import os
import time
import sys
import keyboard
import subprocess  # Import subprocess to handle processes

main_path = r"C:\Users\Justin\OneDrive\Documents\python stuff\main.py"

def exit_program(process):
    print("Exiting program...")
    process.kill()  # Kill the subprocess (main.py)
    sys.exit()  # Exit the current script

# Register the hotkey (Ctrl + Alt + A)
keyboard.add_hotkey('ctrl+alt+a', lambda: exit_program(process))

for i in range(10):  # Runs the script 5 times
    process = subprocess.Popen(['python', main_path])  # Start main.py as a subprocess
    print(f"Run Number:{i}")
    process.wait()  # Wait for main.py to finish before continuing
    time.sleep(10)  # Optional: adds a delay between executions
