from evdev import InputDevice, ecodes
import subprocess
import threading
import logging


logging.basicConfig(level=logging.INFO)


"""
# Change the TOUCHPAD_DEVICE value to the correct path of your touchpad

You can find the path by the following steps:
* run `cat /proc/bus/input/devices`
* find the touchpad device in the list, by looking for the keyword "Touchpad" or similar on the "Name" field
* look for the "Handlers" field and find the corresponding event number (e.g. "event6")
* the path should be "/dev/input/eventX", where X is the event number found
"""
TOUCHPAD_DEVICE = "/dev/input/event6"

FINGERS_CONFIGURED = 3


def monitor_touchpad():
    """Monitor touchpad events and identify gestures"""

    try:
        touchpad = InputDevice(TOUCHPAD_DEVICE)
        logging.info(f"Monitoring touchpad at {TOUCHPAD_DEVICE}")
    except FileNotFoundError:
        logging.error(f"Touchpad device not found at {TOUCHPAD_DEVICE}")
        return

    active_slots = set()
    events = []
    fingers_used = 0

    current_slot = None

    for event in touchpad.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_MT_SLOT:
                current_slot = event.value
            elif event.code == ecodes.ABS_MT_TRACKING_ID:
                if current_slot is not None:
                    if event.value == -1:  # finger lifted
                        active_slots.discard(current_slot)
                    else:  # finger touched
                        active_slots.add(current_slot)
            events.append(event)

        fingers_used = max(fingers_used, len(active_slots))

        if len(active_slots) == 0 and events:
            if fingers_used == FINGERS_CONFIGURED:
                process_gesture(events)
            events = []
            fingers_used = 0

def process_gesture(events):
    """Process events from the touchpad to translate into gestures"""

    x_coords = [e.value for e in events if e.code == ecodes.ABS_MT_POSITION_X]
    y_coords = [e.value for e in events if e.code == ecodes.ABS_MT_POSITION_Y]

    # insuficient data
    if not x_coords or not y_coords:
        return

    x_movement = x_coords[-1] - x_coords[0]
    y_movement = y_coords[-1] - y_coords[0]

    # Horizontal moves -- uncomment to enable
    # if abs(x_movement) > abs(y_movement):
    #     if x_movement > 0:
    #         # right
    #         _execute_command("xdotool key ctrl+alt+Right")
    #     else:
    #         # left
    #         _execute_command("xdotool key ctrl+alt+Left")

    if y_movement < 0:
        # up
        _execute_command("xdotool key super")
    else:
        # down
        _execute_command("xdotool key super")


def _execute_command(command):
    subprocess.run(command, shell=True)


if __name__ == "__main__":
    thread = threading.Thread(target=monitor_touchpad)
    thread.daemon = True
    thread.start()

    print("Press Ctrl+C to exit")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nExiting...")