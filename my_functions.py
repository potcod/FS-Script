import cv2
import numpy as np
import mss
import pyautogui
import time
import pydirectinput  # Import PyDirectInput for DirectInput compatibility
import my_functions
import ctypes
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
def cycle_tabs():
    print("Cycling between tabs...")
    alt_tab()  # Switch to Roblox
    pydirectinput.mouseDown(button='left')
    time.sleep(2)  # Ensure Roblox window is fully focused
    pydirectinput.mouseUp(button='left')

def alt_tab():
    print("Switching tabs to Roblox...")
    pyautogui.hotkey('alt', 'tab')  
    time.sleep(1)  
    pyautogui.hotkey('alt', 'tab')  
    time.sleep(1)  
    print("Now focused on Roblox.")

def click_and_drag(start_x, start_y, end_x, end_y):
    """Simulates a click and drag from (start_x, start_y) to (end_x, end_y)."""
    pydirectinput.moveTo(start_x, start_y)
    time.sleep(0.1)  
    pydirectinput.mouseDown(button='left')
    pydirectinput.moveTo(end_x, end_y)
    time.sleep(0.2)  
    pydirectinput.mouseUp(button='left')

def click_drag_and_move_camera(start_x, start_y):
    """
    Moves the camera by dragging the mouse incrementally.
    """
    move_step = 2  
    end_x = start_x + move_step
    end_y = start_y

    click_and_drag(start_x, start_y, end_x, end_y)
    
    return end_x, end_y  

def rotate_camera(rotation_count):
    """
    Rotates the camera 360 degrees in 10 steps.
    Returns updated rotation count.
    """
    if rotation_count >= 6:
        reset_character()
        print("Rotation complete.")
        return 0  # Reset the counter

    print(f"Rotating camera {rotation_count + 1}/10")

    pydirectinput.keyDown("right")  
    time.sleep(0.4)
    pydirectinput.keyUp("right")

    return rotation_count + 1  # Return updated count


def reset_character():
    """
    Simulates pressing Esc -> R -> Enter to reset the character in Roblox.
    """
    print("Resetting character in Roblox...")
    pydirectinput.press("esc")  
    time.sleep(0.5)  
    pydirectinput.press("r")  
    time.sleep(0.5)
    pydirectinput.press("enter")  
    time.sleep(4.0)  
    print("Character has been reset.")

def move_and_click(coords, delay=4):
    time.sleep(delay)
    for x, y in coords:
        pyautogui.moveTo(x, y)
        time.sleep(0.5)  # Optionally add a small delay before clicking
        pydirectinput.mouseDown(button='left')
        time.sleep(0.3)
        pydirectinput.mouseUp(button='left')
        time.sleep(delay)  # Wait for specified delay in seconds

def capture_screen():
    """Captures the screen from the second monitor and returns a grayscale image."""
    with mss.mss() as sct:
        monitor = sct.monitors[2]  # Adjust monitor index if needed
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
        return img, img_gray  # Return both color and grayscale image
    
def get_template_position(template):
    """Finds the template position on the second monitor using template matching."""
    img, img_gray = my_functions.capture_screen()

    # Perform template matching
    result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Debug: check the result values
    print(f"Max Val: {max_val}, Min Val: {min_val}")

    # Only return position if the match is above a certain threshold
    if max_val > 0.30:  # Adjust threshold if needed
        return max_loc, img  # Return top-left corner of the match along with the color image
    return None, img  # No match found, return the original image

def get_average_location(keypoints_screen):
    """
    Calculates the average (centroid) location of all keypoints,
    filtering out outliers.
    :param keypoints_screen: List of cv2.KeyPoint objects.
    :return: Tuple (avg_x, avg_y) representing the centroid location.
    """
    if not keypoints_screen:
        print("No keypoints found!")
        return None  # Return None if no keypoints are available

    # Extract x and y coordinates from keypoints
    x_coords = [kp.pt[0] for kp in keypoints_screen]
    y_coords = [kp.pt[1] for kp in keypoints_screen]
    
    # Remove outliers
    filtered_x = remove_outliers(x_coords)
    filtered_y = remove_outliers(y_coords)
    
    if not filtered_x or not filtered_y:
        print("All keypoints removed as outliers!")
        return None
    
    # Compute the mean of filtered x and y coordinates
    avg_x = np.mean(filtered_x)
    avg_y = np.mean(filtered_y)
    
    return avg_x, avg_y

def remove_outliers(data, threshold=1.5):
    """
    Removes outliers using the interquartile range (IQR) method.
    :param data: List of numeric values.
    :param threshold: Multiplier for IQR to define outliers.
    :return: Filtered list without outliers.
    """
    if len(data) < 3:
        return data  # Not enough data to filter
    
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - (threshold * iqr)
    upper_bound = q3 + (threshold * iqr)
    
    return [x for x in data if lower_bound <= x <= upper_bound]

'''
def recenter(kp_screen):
    avg_x, avg_y = my_functions.get_average_location(kp_screen)
    int_x = avg_x.astype(int)
    int_y = avg_y.astype(int)
    start_x, start_y = pyautogui.position()
    # Adjust for second monitor offset (1980px to the right)
    high_den_x = int_x   # Add 1980px to convert to full-screen coordinates
    high_den_y = int_y   # Centering the mouse on the template
    d_den_x = high_den_x - start_x
    d_den_y = high_den_y - start_y
    print(f"avg:  {high_den_x//4, high_den_y//4}")

    for i in range(1):
        move_mouse(d_den_x//4, d_den_y//4)
        time.sleep(0.4)
'''

def recenter(kp_screen):
    avg_x, avg_y = my_functions.get_average_location(kp_screen)
    int_x = avg_x.astype(int)
    int_y = avg_y.astype(int)
    start_x, start_y = pyautogui.position()
    # Adjust for second monitor offset (1980px to the right)
    target_x = int_x + 1980 # Add 1980px to convert to full-screen coordinates
    target_y = int_y   # Centering the mouse on the template
    dx = target_x - start_x
    dy = target_y - start_y
    print(f"Target:  {target_x, target_y}")
    print(f"dx, dy:  {dx, dy}")
    print(f"Start:  {start_x, start_y}")

    for i in range(1):
        move_mouse(dx//4, dy//4)
        time.sleep(0.4)

# Function to move mouse relatively using ctypes
def move_mouse(dx, dy):
    """Moves the mouse dx, dy pixels from its current position."""
    ii_ = Input_I()
    ii_.mi = MouseInput(dx, dy, 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(ctypes.c_ulong(0)))
    input_ = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.byref(input_), ctypes.sizeof(input_))