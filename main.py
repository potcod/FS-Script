import cv2
import numpy as np
import mss
import pyautogui
import time
import pydirectinput
import threading
from queue import Queue
import my_functions
import ctypes 
import os
import math
import webbrowser
import pygetwindow as gw
import screeninfo
import random

# this is most updated
# Path to the reference image (with correct extension)
image_path = r"C:\Users\Justin\OneDrive\Documents\python stuff\reference.jpg.jpg"
reference_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

# Load the template image (adjust the path)
template_path = r"C:\Users\Justin\OneDrive\Documents\python stuff\template.jpg"
template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

# Global Variables for the mouse position
start_x, start_y = pyautogui.position()  # Get current mouse position

#Flags
task_1_completed = False

task_2_completed = False
capture_running = True  # Global flag to control the capture thread


# Global counter for camera rotations
rotation_count = 6

# Track the time when the else condition starts
else_condition_start = None  
else_condition_active = False  # Flag to track if the condition is ongoing

# Variable to store filtered matches
filtered_matches = []

if reference_image is None:
    print("Failed to load the reference image. Please check the file path.")
    exit()

# Initialize ORB detector
orb = cv2.ORB_create()
kp_ref, des_ref = orb.detectAndCompute(reference_image, None)

if len(kp_ref) == 0:
    print("No keypoints found in the reference image!")
else:
    print(f"Found {len(kp_ref)} keypoints in the reference image.")

#CTYPE movement stuff
w, h = template.shape[::-1]  # Get template dimensions
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

#Mouse scroll
MOUSEEVENTF_WHEEL = 0x0800

# Function to simulate mouse scroll
def scroll(amount):
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount, 0)

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Constants for mouse movement
MOUSEEVENTF_MOVE = 0x0001

# Function to move mouse relatively using ctypes
def move_mouse(dx, dy):
    """Moves the mouse dx, dy pixels from its current position."""
    ii_ = Input_I()
    ii_.mi = MouseInput(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(ctypes.c_ulong(0)))
    input_ = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.byref(input_), ctypes.sizeof(input_))

# Function to capture and display the screen with keypoints
def capture_and_display():
    global kp_screen, img_bgr, filtered_matches

    with mss.mss() as sct:
        monitor = sct.monitors[2]  # Change this to monitor 2 (index 2)

        while capture_running:
            # Capture the screen
            screenshot = sct.grab(monitor)

            # Convert screenshot to a numpy array (OpenCV format)
            img = np.array(screenshot)

            # Convert the image from RGB (screen capture) to BGR (OpenCV format)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            # Convert the captured image to grayscale for feature matching
            gray_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            # Find keypoints and descriptors in the screen capture
            kp_screen, des_screen = orb.detectAndCompute(gray_img, None)

            # Filter out keypoints in the top 20% and bottom 10% of the screen
            screen_height, screen_width = img_bgr.shape[:2]
            top_margin = 0.15  # 20% of the screen height for the top region
            bottom_margin = 0.15  # 10% of the screen height for the bottom region

            # Keep keypoints that are NOT in the top 20% or bottom 10% of the screen
            filtered_kp_screen = []
            for kp in kp_screen:
                x, y = kp.pt
                # Exclude keypoints that are in the top 20% or bottom 10% of the screen
                if y > (screen_height * top_margin) and y < (screen_height * (1 - bottom_margin)):  # Not in top 20% or bottom 10%
                    filtered_kp_screen.append(kp)

            # Filter keypoints in the reference image as well
            filtered_kp_ref = []
            for kp in kp_ref:
                x, y = kp.pt
                # Exclude keypoints that are in the top 20% or bottom 10% of the reference image
                if y > (reference_image.shape[0] * top_margin) and y < (reference_image.shape[0] * (1 - bottom_margin)):
                    filtered_kp_ref.append(kp)

            # Use BFMatcher to match descriptors between the reference and the screen capture
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des_ref, des_screen)

            # Sort matches based on distance (lower distance is better)
            matches = sorted(matches, key=lambda x: x.distance)

            # Filter out matches based on the filtered keypoints
            filtered_matches = []
            for match in matches:
                ref_idx = match.queryIdx  # Reference keypoint index
                screen_idx = match.trainIdx  # Screen keypoint index

                # Check if both keypoints are in the filtered set of keypoints
                if kp_ref[ref_idx] in filtered_kp_ref and kp_screen[screen_idx] in filtered_kp_screen:
                    filtered_matches.append(match)

            # Display keypoints and matches
            reference_kp_img = cv2.cvtColor(reference_image, cv2.COLOR_GRAY2BGR)  # Convert to color for displaying
            reference_kp_img = cv2.drawKeypoints(reference_kp_img, filtered_kp_ref, None, color=(0, 255, 0), flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)

            img_bgr_with_kp = img_bgr.copy()
            screen_kp_img = cv2.drawKeypoints(img_bgr_with_kp, filtered_kp_screen, None, color=(0, 255, 0), flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS)

            # Show images
            #cv2.imshow("Reference Image with Keypoints", reference_kp_img)
            #cv2.imshow("Screen Capture with Keypoints", screen_kp_img)

            # Delay to make sure the window doesn't freeze and gives a smooth update
            cv2.waitKey(1)

# Start the screen capture and keypoint detection in a separate thread
capture_thread = threading.Thread(target=capture_and_display, daemon=True)
capture_thread.start()

# Main task logic
my_functions.cycle_tabs()
my_functions.alt_tab()

coordinates = [
    (948,91),
]
print("Switching tabs to Roblox...")
pyautogui.hotkey('alt', 'tab')  
time.sleep(1)  
print("Now focused on Roblox.")
my_functions.move_and_click(coordinates, delay=3)

time.sleep(180)  

my_functions.cycle_tabs()

# Main loop to perform incremental camera movement
while task_1_completed == False:
    matches = filtered_matches  # Use the directly accessed filtered matches

    # Check if there are enough matches for performing tasks
    if len(matches) >= 90:  # If there are more than or equal to 100 matches
        print("Matches > 100, performing task...")

        if not else_condition_active:
            else_condition_start = time.time()  # Start timer
            else_condition_active = True  

        # Check if 10 seconds have passed
        if else_condition_active and time.time() - else_condition_start > 5:
            print("Else condition met for more than 10 seconds! Moving cursor to highest density.")
            else_condition_start = None  # Reset timer
            else_condition_active = False  # Reset flag
            my_functions.recenter(kp_screen)
                
            pydirectinput.keyDown("d")
            time.sleep(2)
            pydirectinput.keyUp("d")
            time.sleep(0.5)
            pydirectinput.keyDown("down")  
            time.sleep(7)
            pydirectinput.keyUp("down")
            my_functions.recenter(kp_screen)
            task_1_completed = True
            capture_running = False
            break  # Break the main loop when the condition is met

    else:
            #print("Matches < 100, rotating camera.")
            # Perform click-and-drag for camera panning if matches < 100
            rotation_count = my_functions.rotate_camera(rotation_count)
            time.sleep(1)  # Make sure the camera rotation is not too fast

    # Delay to prevent the loop from running too fast and checking the matches continuously
    print(f"sleepy")

time.sleep(0.5)

# Main loop for continuous template matching
while task_2_completed == False:
    # Get current mouse position dynamically
    start_x, start_y = pyautogui.position()

    detected_pos, img = my_functions.get_template_position(template)
    if task_2_completed == True:
        print("Task 2 completed.")
        break

    if detected_pos:
        detected_x, detected_y = detected_pos
        print(f"Template found at position: {detected_x}, {detected_y} (Relative to second monitor)")

        # Adjust for second monitor offset (1980px to the right)
        target_x = 1980 + detected_x + w // 2  # Add 1980px to convert to full-screen coordinates
        target_y = detected_y + h // 2  # Centering the mouse on the template

        print(f"Target position after adjusting (full screen): ({target_x}, {target_y})")

        # Calculate relative movement from current mouse position
        dx = target_x - start_x  # Difference between target position and current mouse position
        dy = target_y - start_y

        # Debugging the relative movement calculation
        print(f"Mouse move calculation: dx = {dx}, dy = {dy}")

        # Move the mouse relative to its current position
        move_mouse(dx//4, dy//4)
        print(f"Moving mouse by: ({dx//4}, {dy//4})")
        time.sleep(1)
        # Draw a rectangle around the detected template
        top_left = (detected_x, detected_y)
        bottom_right = (detected_x + w, detected_y + h)
        cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)  # Green rectangle

        if (math.sqrt((dx//2)**2 + (dy//2)**2) <= 3):
            time.sleep(2)
            move_mouse(160, 160)
            task_2_completed = True
            break

        # Show the image with the matched template
        #cv2.imshow("Template Matching", img)
    else:
        print("Template not found. Retrying...")

#Tiny Task
#coordinates = [(1060,752),]
#print("Switching tabs to Roblox...")
time.sleep(5)
print("Tiny task")
pydirectinput.keyDown('ctrl')  
pydirectinput.keyDown('shift')  
pydirectinput.keyDown('alt')  
pydirectinput.keyDown('p') 
time.sleep(0.5)
pydirectinput.keyUp('ctrl')  
pydirectinput.keyUp('shift')  
pydirectinput.keyUp('alt')  
pydirectinput.keyUp('p') 
time.sleep(80)  

#This one will click ready every 5 seconds
scroll(-120)
target_position = [(3769,961)]
duration = 310
# Move the mouse to each position and perform actions
for x, y in target_position:
    for i in range(duration):
        # Move the mouse directly to the target position
        print(f"Iteration:{i} / {duration}")
        pydirectinput.moveTo(x, y, duration=0.3)
        time.sleep(0.3)  # Allow cursor to settle
        
        # Slightly nudge the mouse before clicking
        pydirectinput.moveRel(1, 1, duration=0.1)
        time.sleep(0.1)  # Extra delay before clicking
        
        pydirectinput.doubleClick()
        time.sleep(8.2)

#'''

#This will go back to the main menu
time.sleep(3)
# Define the coordinates to move the mouse to
target_positions = [
    (1992, 960),
    (2370, 979),
    (2985, 800)
]

# Move the mouse to each position and perform actions
for i in range(4):
    for x, y in target_positions:
        # Simulate a more human-like movement using pydirectinput
        pydirectinput.moveTo(x + random.randint(-5, 5), y + random.randint(-5, 5), duration=random.uniform(0.2, 0.5))
        time.sleep(random.uniform(0.2, 0.4))  # Allow cursor to settle
        
        # Slightly nudge the mouse before clicking
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        pydirectinput.moveRel(offset_x, offset_y, duration=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.1, 0.2))  # Extra delay before clicking
        
        pydirectinput.doubleClick()
        time.sleep(random.uniform(4.5, 5.5))

