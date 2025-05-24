import pyautogui

print("Press Enter to get the mouse position. Type 'exit' and press Enter to quit.")

while True:
  user_input = input()
  if user_input.lower() == 'exit':
    print("Exiting...")
    break
  x, y = pyautogui.position()
  print(f"Mouse position: ({x}, {y})")