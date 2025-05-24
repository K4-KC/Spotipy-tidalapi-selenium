import pyautogui
import time

# -- Setup: optional PyAutoGUI settings --
pyautogui.PAUSE = 0.5   # pause after each PyAutoGUI call for safety
pyautogui.FAILSAFE = True  # move mouse to corner to abort

# Prompt user to open Brave and load the site
input("Open Brave and navigate to https://doubledouble.top. Then press Enter to start setup...")

# Capture coordinates of the input box, download button, save button by user hover
print("Hover mouse over the Tidal link input box and press Enter")
input()  # wait for user
input_box = pyautogui.position()  # get current mouse coords
print(f"Input box at {input_box}")

print("Hover mouse over the 'Download' button and press Enter")
input()
download_button = pyautogui.position()
print(f"Download button at {download_button}")

# # Capture Save message location and color for detection
# print("Hover mouse over the 'Save' button and press Enter")
# input()
# save_button = pyautogui.position()
# save_button_color = (56, 56, 56)  # dark gray color in RGB
# print(f"Save button at {save_button}")
save_button = (2363, 690)
save_button_color = (56, 56, 56)

# Capture Success message location and color for detection
print("Hover mouse over the center of the green success box and press Enter")
input()
success_pos = pyautogui.position()
success_color = (29, 185, 84)  # green color in RGB
print(f"Success position at {success_pos}")

# # Capture error message location and color for detection
# print("Hover mouse over the center of the red error box and press Enter")
# input()
# error_pos = pyautogui.position()
# error_color = (255, 0, 0)  # red color in RGB
# print(f"Error position at {error_pos}")

error_pos = success_pos
error_color = (255, 0, 0)  # red color in RGB
print(f"Error position at {error_pos}")

# List of Tidal song URLs to process (modify or load from file as needed)
# tidal_links = [
#     "https://tidal.com/track/422672255",  # example links
#     "https://tidal.com/track/248133980",
#     # add more links here...
# ]



def is_save_button_visible(pos, color, tolerance=10):
    x, y = pos
    return pyautogui.pixelMatchesColor(x, y, color, tolerance=tolerance)

def is_success_visible(pos, color, tolerance=10):
    x, y = pos
    return pyautogui.pixelMatchesColor(x, y, color, tolerance=tolerance)

def is_error_visible(pos, color, tolerance=10):
    x, y = pos
    return pyautogui.pixelMatchesColor(x, y, color, tolerance=tolerance)

print("Starting automation of links...")
for link in tidal_links:
    # Click input box, clear any existing text, and type the new link
    pyautogui.click(input_box)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.typewrite(link, interval=0.05)
    
    link_downloaded_and_saved = False
    attempts = 0
    max_attempts = 3
    signal_timeout = 300  # seconds to wait for success or error signal

    while attempts < max_attempts:
        attempts += 1
        print(f"Attempt {attempts}/{max_attempts} for link: {link}")
        pyautogui.click(download_button)
        
        current_attempt_succeeded = False
        current_attempt_failed_with_error = False
        link_ripped = False

        wait_start_time = time.time()
        while time.time() - wait_start_time < signal_timeout:
            if is_success_visible(success_pos, success_color) or link_ripped:
                print(f"Success detected for link {link} on attempt {attempts}.")
                link_ripped = True
                # click save button when you see save message
                if is_save_button_visible(save_button, save_button_color):
                    pyautogui.click(save_button)
                    print(f"Save button clicked for link: {link}")
                    link_downloaded_and_saved = True
                    current_attempt_succeeded = True
                    break  # from inner signal_wait_loop
            
            if is_error_visible(error_pos, error_color):
                print(f"Error detected on attempt {attempts} for link {link}.")
                current_attempt_failed_with_error = True
                break  # from inner signal_wait_loop
            
            time.sleep(0.5)  # Poll every half second

        if current_attempt_succeeded:
            break  # from attempts loop, this link is done

        if current_attempt_failed_with_error:
            if attempts < max_attempts:
                print("Retrying link...")
                time.sleep(1)  # Brief pause before retrying
                # Link input is handled at the start of the outer loop,
                # so we just continue to retry the download click.
            else:
                print(f"Max attempts reached for {link} due to persistent error. Skipping save.")
            # Continue to next attempt or break if max attempts reached
            if attempts >= max_attempts:
                break 
            else:
                continue
        
        # If neither success nor error was visible (timeout of inner loop)
        if not current_attempt_succeeded and not current_attempt_failed_with_error:
            print(f"Timeout waiting for success/error signal on attempt {attempts} for link {link}.")
            if attempts < max_attempts:
                print("Retrying link...")
                time.sleep(1)
            else:
                print(f"Max attempts reached for {link} due to persistent timeout. Skipping save.")
            # Continue to next attempt or break if max attempts reached
            if attempts >= max_attempts:
                break
            else:
                continue

    if link_downloaded_and_saved:
        print(f"Successfully processed and saved: {link}")
        # Wait a bit for the download to actually complete on the system
        time.sleep(5) 
    else:
        print(f"Failed to download/save link after {max_attempts} attempts: {link}")

print("Done processing all links.")
