import os
import time

import requests
from dotenv import load_dotenv

from pixoo import Pixoo

# Load .env variables
load_dotenv()


def defined_value(value, default):
    return default if value is None else value


def retrieve_current_kwh_usage():
    response = requests.get(f'http://192.168.50.45/api/v1/data')
    data = response.json()

    return data['active_power_w']


def main():
    print('[.] Booting..')

    # Verify if the ip address is set, otherwise None
    ip_address = os.environ.get('PIXOO_IP_ADDRESS')
    if ip_address is None:
        print('[!] No IP address has been provided, will attempt to find device on network')

    # Pretty colors
    green = (99, 199, 77)
    red = (255, 0, 68)
    white = (255, 255, 255)

    brightness = int(defined_value(os.environ.get('BRIGHTNESS'), 100))
    simulated = int(defined_value(os.environ.get('SIMULATED'), 0)) == 1
    timeout = int(defined_value(os.environ.get('TIMEOUT'), 60))

    if simulated:
        print('[.] Starting in simulation mode')
    else:
        print('[.] Starting in connected mode')

    # Draw a blank screen for now
    pixoo = Pixoo(ip_address)
    pixoo.draw_image('background.png')
    pixoo.set_brightness(brightness)  # Only used sometimes if the screen isn't bright enough
    pixoo.draw_text('kWh', (8, 40), white)
    pixoo.draw_text('-', (53, 40), white)
    pixoo.push()

    print('[.] Starting update loop in 2 seconds')
    time.sleep(2)

    buffer = []
    while True:
        try:
            # Assure a connection to the device (if the program keeps running without the screen being on
            # this will make sure it connects as soon as possible in exchange for a minor lag because of another call
            if not pixoo.validate_connection():
                time.sleep(60)
                continue

            # Place the background again first,
            # No need to clear since it's screen sized
            pixoo.draw_image('background.png')

            current_kwh_usage = retrieve_current_kwh_usage()
            current_kwh_usage_string = str(current_kwh_usage)

            pixoo.draw_text('kWh', (8, 40))
            pixoo.draw_text(current_kwh_usage_string, (53 - (len(current_kwh_usage_string) - 1) * 4, 40))

            # Keep it at most a certain length
            buffer.insert(0, current_kwh_usage)
            buffer = buffer[:47]
            start = (55, 35)

            for index, former_kwh_usage in enumerate(buffer):
                offset = int(former_kwh_usage / 100)
                pixoo.draw_pixel((start[0] - index, start[1] - offset), green)

            # Push to the display
            pixoo.push()
            time.sleep(timeout)
        except KeyboardInterrupt:
            print("[.] Shutting down..")
            return


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
