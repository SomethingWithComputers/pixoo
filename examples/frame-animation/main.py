import os
import time

from dotenv import load_dotenv

from pixoo import Pixoo, FrameAnimatedImage

# Load .env variables
load_dotenv()


def main():
    print('[.] Booting..')

    # Verify if the ip address is set, can't default this one
    ip_address = os.environ.get('PIXOO_IP_ADDRESS')
    if ip_address is None:
        print('[x] Please set the `PIXOO_IP_ADDRESS` value in the .env file')
        return

    # Set up a connection and show the background
    pixoo = Pixoo()

    background = pixoo.load_image('assets/background.png')
    clanker_animation = FrameAnimatedImage(pixoo, 'assets/clanker-success_15x1.png', 10, 15)

    print('[.] Starting loop in 2 seconds')
    time.sleep(2)
    timeout = 1 / 3  # 3fps
    while True:
        pixoo.draw_image(background)

        clanker_animation.draw_current_frame((27, 20))
        clanker_animation.move_to_next_frame()
        # Push to the display
        pixoo.push()

        # Wait a bit before updating everything
        time.sleep(timeout)


if __name__ == '__main__':
    main()
