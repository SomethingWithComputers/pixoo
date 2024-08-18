import os
import time

import requests
from dotenv import load_dotenv

from pixoo import Pixoo, SimulatorConfiguration

# Load .env variables
load_dotenv()


def defined_value(value, default):
    return default if value is None else value


def ping():
    response = requests.get('https://api.coingecko.com/api/v3/ping')
    return 'gecko_says' in response.json()


def retrieve_fah_score(user_id):
    response = requests.get(f'https://api2.foldingathome.org/uid/{user_id}')
    return response.json()['score']


def retrieve_current_price():
    response = requests.get('https://api.coingecko.com/api/v3/coins/banano')
    data = response.json()

    currency = 'usd'
    market_data = data['market_data']

    return market_data['current_price'][currency], \
        market_data['price_change_percentage_24h_in_currency'][currency]


def main():
    print('[.] Booting..')

    if ping():
        print('[.] CoingGecko API reachable')
    else:
        print(
            '[x] CoinGecko API is not reachable. Perhaps check your internet settings')
        return

    # Verify if the ip address is set, can't default this one
    ip_address = os.environ.get('PIXOO_IP_ADDRESS')
    if ip_address is None:
        print('[x] Please set the `PIXOO_IP_ADDRESS` value in the .env file')
        return

    # A pleasant green color. Like a yet-to-be-ripe banano
    green = (99, 199, 77)
    red = (255, 0, 68)
    white = (255, 255, 255)

    # Retrieve some config
    timeout = int(defined_value(os.environ.get('TIMEOUT'), 3600))
    user_id = defined_value(os.environ.get('FAH_USER_ID'), '501878621')

    # Set up a connection and show the background
    pixoo = Pixoo(ip_address, simulated=True, simulation_config=SimulatorConfiguration(4))
    pixoo.draw_image('background.png')
    # pixoo.set_brightness(100) # Only used sometimes if the screen isn't bright enough
    pixoo.draw_text('-----', (20, 49), green)
    pixoo.draw_text('------', (20, 43), green)
    pixoo.draw_text('-------------', (7, 57), green)
    pixoo.push()

    print('[.] Starting update loop in 2 seconds')
    time.sleep(2)
    while True:

        # Retrieve the current price and change percentage from the coingecko API
        current_price, change_percentage = retrieve_current_price()

        # Retrieve the current F@H score from their sort-of API
        score = retrieve_fah_score(user_id)

        # Determine the color and symbol
        if change_percentage >= 0:
            color = green
            symbol = '+'
        else:
            color = red
            symbol = ''

        # Place the background again first,
        # no need to clear since it's screen sized
        pixoo.draw_image('background.png')

        # Draw the change percentage
        pixoo.draw_text(f'{symbol}{change_percentage:.1f}%', (20, 49), color)

        # Draw current price
        pixoo.draw_text(f'${current_price:.3f}', (20, 43), color)

        # Draw current F@H stats
        pixoo.draw_text(f'F@H {score}', (7, 57), green)

        # Push to the display
        pixoo.push()

        # Wait a bit before updating everything
        time.sleep(timeout)


if __name__ == '__main__':
    main()
