import base64
import json

import requests
from PIL import Image, ImageOps

from .simulator import Simulator
from .. import Palette, SimulatorConfiguration, ImageResampleMode, TextScrollDirection
from ..constants.font import retrieve_glyph
from ..utilities import minimum_amount_of_steps, round_location, lerp_location, clamp_color, rgb_to_hex_color, clamp


class Pixoo:
    __buffer = []
    __buffers_send = 0
    __counter = 0
    __refresh_counter_limit = 32
    __simulator = None

    def __init__(self, ip_address=None, size=64, debug=False, refresh_connection_automatically=True,
                 simulated=False,
                 simulation_config=SimulatorConfiguration()):
        assert size in [16, 32, 64], \
            'Invalid screen size in pixels given. ' \
            'Valid options are 16, 32, and 64'

        self.simulated = simulated

        # Attempt to load the IP if it's not
        if ip_address is None:
            self.ip_address = self.find_local_device_ip()
        else:
            self.ip_address = ip_address

        self.debug = debug
        self.refresh_connection_automatically = refresh_connection_automatically
        self.size = size

        # Total number of pixels
        self.pixel_count = self.size * self.size

        # Generate URL
        self.__url = 'http://{0}/post'.format(self.ip_address)

        # Prefill the buffer
        self.fill()

        if not self.validate_connection():
            print("[x] No connection could be made. Verify all settings")
            return

        # Retrieve the counter
        self.__load_counter()

        # Resetting if needed
        if self.refresh_connection_automatically and self.__counter > self.__refresh_counter_limit:
            self.__reset_counter()

        # We're going to need a simulator
        if self.simulated:
            self.__simulator = Simulator(self, simulation_config)

    def clear(self, rgb=Palette.BLACK):
        self.fill(rgb)

    def clear_rgb(self, r, g, b):
        self.fill_rgb(r, g, b)

    def draw_character(self, character, xy=(0, 0), rgb=Palette.WHITE):
        matrix = retrieve_glyph(character)
        if matrix is not None:
            for index, bit in enumerate(matrix):
                if bit == 1:
                    local_x = index % 3
                    local_y = int(index / 3)
                    self.draw_pixel((xy[0] + local_x, xy[1] + local_y), rgb)

    def draw_character_at_location_rgb(self, character, x=0, y=0, r=255, g=255,
                                       b=255):
        self.draw_character(character, (x, y), (r, g, b))

    def draw_filled_rectangle(self, top_left_xy=(0, 0), bottom_right_xy=(1, 1),
                              rgb=Palette.BLACK):
        for y in range(top_left_xy[1], bottom_right_xy[1] + 1):
            for x in range(top_left_xy[0], bottom_right_xy[0] + 1):
                self.draw_pixel((x, y), rgb)

    def draw_filled_rectangle_from_top_left_to_bottom_right_rgb(self,
                                                                top_left_x=0,
                                                                top_left_y=0,
                                                                bottom_right_x=1,
                                                                bottom_right_y=1,
                                                                r=0, g=0, b=0):
        self.draw_filled_rectangle((top_left_x, top_left_y),
                                   (bottom_right_x, bottom_right_y), (r, g, b))

    def draw_image(self, image_path_or_object, xy=(0, 0),
                   image_resample_mode=ImageResampleMode.PIXEL_ART,
                   pad_resample=False):
        image = image_path_or_object if isinstance(image_path_or_object,
                                                   Image.Image) else Image.open(
            image_path_or_object)
        size = image.size
        width = size[0]
        height = size[1]

        # See if it needs to be scaled/resized to fit the display
        if width > self.size or height > self.size:
            if pad_resample:
                image = ImageOps.pad(image, (self.size, self.size),
                                     image_resample_mode)
            else:
                image.thumbnail((self.size, self.size), Image.Resampling(image_resample_mode))

            if self.debug:
                print(
                    f'[.] Resized image to fit on screen (saving aspect ratio): "{image_path_or_object}" ({width}, {height}) '
                    f'-> ({image.size[0]}, {image.size[1]})')

        # Convert the loaded image to RGB
        rgb_image = image.convert('RGB')

        # Iterate over all pixels in the image that are left and buffer them
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                location = (x, y)
                placed_x = x + xy[0]
                if self.size - 1 < placed_x or placed_x < 0:
                    continue

                placed_y = y + xy[1]
                if self.size - 1 < placed_y or placed_y < 0:
                    continue

                self.draw_pixel((placed_x, placed_y),
                                rgb_image.getpixel(location))

    def draw_image_at_location(self, image_path_or_object, x, y,
                               image_resample_mode=ImageResampleMode.PIXEL_ART):
        self.draw_image(image_path_or_object, (x, y), image_resample_mode)

    def draw_line(self, start_xy, stop_xy, rgb=Palette.WHITE):
        line = set()

        # Calculate the amount of steps needed between the points to draw a nice line
        amount_of_steps = minimum_amount_of_steps(start_xy, stop_xy)

        # Iterate over them and create a nice set of pixels
        for step in range(amount_of_steps):
            if amount_of_steps == 0:
                interpolant = 0
            else:
                interpolant = step / amount_of_steps

            # Add a pixel as a rounded location
            line.add(round_location(lerp_location(start_xy, stop_xy, interpolant)))

        # Draw the actual pixel line
        for pixel in line:
            self.draw_pixel(pixel, rgb)

    def draw_line_from_start_to_stop_rgb(self, start_x, start_y, stop_x, stop_y,
                                         r=255, g=255, b=255):
        self.draw_line((start_x, start_y), (stop_x, stop_y), (r, g, b))

    def draw_pixel(self, xy, rgb):
        # If it's not on the screen, we're not going to bother
        if xy[0] < 0 or xy[0] >= self.size or xy[1] < 0 or xy[1] >= self.size:
            if self.debug:
                limit = self.size - 1
                print(
                    f'[!] Invalid coordinates given: ({xy[0]}, {xy[1]}) (maximum coordinates are ({limit}, {limit})')
            return

        # Calculate the index
        index = xy[0] + (xy[1] * self.size)

        # Color it
        self.draw_pixel_at_index(index, rgb)

    def draw_pixel_at_index(self, index, rgb):
        # Validate the index
        if index < 0 or index >= self.pixel_count:
            if self.debug:
                print(f'[!] Invalid index given: {index} (maximum index is {self.pixel_count - 1})')
            return

        # Clamp the color, just to be safe
        rgb = clamp_color(rgb)

        # Move to place in array
        index = index * 3

        self.__buffer[index] = rgb[0]
        self.__buffer[index + 1] = rgb[1]
        self.__buffer[index + 2] = rgb[2]

    def draw_pixel_at_index_rgb(self, index, r, g, b):
        self.draw_pixel_at_index(index, (r, g, b))

    def draw_pixel_at_location_rgb(self, x, y, r, g, b):
        self.draw_pixel((x, y), (r, g, b))

    def draw_text(self, text, xy=(0, 0), rgb=Palette.WHITE):
        for index, character in enumerate(text):
            self.draw_character(character, (index * 4 + xy[0], xy[1]), rgb)

    def draw_text_at_location_rgb(self, text, x, y, r, g, b):
        self.draw_text(text, (x, y), (r, g, b))

    def fill(self, rgb=Palette.BLACK):
        self.__buffer = []
        rgb = clamp_color(rgb)
        for index in range(self.pixel_count):
            self.__buffer.extend(rgb)

    def fill_rgb(self, r, g, b):
        self.fill((r, g, b))

    def find_local_device_ip(self):
        if self.simulated:
            return None

        response = requests.post('https://app.divoom-gz.com/Device/ReturnSameLANDevice')
        data = response.json()
        if data['ReturnCode'] != 0:
            self.__error(data)

        if len(data['DeviceList']) >= 1:
            if len(data['DeviceList']) > 1:
                print(
                    f'[!] Multiple devices found on local LAN, connecting to the first one (override this by '
                    f'providing a device_name in the constructor): {0})'.format(
                        data['DeviceList'][0]['DeviceName']))

            return data['DeviceList'][0]['DevicePrivateIP']

        print('[x] No devices found on local LAN')
        return None

    def get_all_device_configurations(self):
        # This won't be possible
        if self.simulated:
            return None

        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/GetAllConf',
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

        return data

    def get_device_time(self):
        # This won't be possible
        if self.simulated:
            return None

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/GetDeviceTime',
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
            return None

        print(data)
        return data

    def play_local_gif(self, file_path):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/PlayTFGif',
            'FileType': 0,
            'FileName': file_path
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def play_local_gif_directory(self, path):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/PlayTFGif',
            'FileType': 1,
            'FileName': path
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def play_net_gif(self, gif_file_url):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/PlayTFGif',
            'FileType': 2,
            'FileName': gif_file_url
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def sound_buzzer(self, active_cycle_time=500, inactive_cycle_time=500, total_time=3000):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/PlayBuzzer',
            'ActiveTimeInCycle': active_cycle_time,
            'OffTimeInCycle': inactive_cycle_time,
            'PlayTotalTime': total_time,
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def push(self):
        self.__send_buffer()

    def reboot(self):
        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/SysReboot'
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def send_text(self, text, xy=(0, 0), color=Palette.WHITE, identifier=1,
                  font=2, width=64,
                  movement_speed=0,
                  direction=TextScrollDirection.LEFT):

        # This won't be possible
        if self.simulated:
            return

        # Make sure the identifier is valid
        identifier = clamp(identifier, 0, 19)

        response = requests.post(self.__url, json.dumps({
            'Command': 'Draw/SendHttpText',
            'TextId': identifier,
            'x': xy[0],
            'y': xy[1],
            'dir': direction,
            'font': font,
            'TextWidth': width,
            'speed': movement_speed,
            'TextString': text,
            'color': rgb_to_hex_color(color)
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def send_text_at_location_rgb(self, text, x=0, y=0, r=255, g=255, b=255, identifier=1, font=2, width=64,
                                  movement_speed=0,
                                  direction=TextScrollDirection.LEFT):
        self.send_text(text, (x, y), (r, g, b), identifier, font, width, movement_speed, direction)

    def set_brightness(self, brightness):
        # This won't be possible
        if self.simulated:
            return

        brightness = clamp(brightness, 0, 100)
        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetBrightness',
            'Brightness': brightness
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_channel(self, channel):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetIndex',
            'SelectIndex': int(channel)
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_clock(self, clock_id):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetClockSelectId',
            'ClockId': clock_id
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_face(self, face_id):
        self.set_clock(face_id)

    def set_high_light_mode(self, on=True):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/SetHighLightMode',
            'Mode': on
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_mirror_mode(self, on=False):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/SetMirrorMode',
            'Mode': on
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_noise_status(self, on=True):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Tools/SetNoiseStatus',
            'NoiseStatus': on
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_score_board(self, blue_score, red_score):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Tools/SetScoreBoard',
            'BlueScore': clamp(blue_score, 0, 999),
            'RedScore': clamp(red_score, 0, 999)
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_screen(self, on=True):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/OnOffScreen',
            'OnOff': 1 if on else 0
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_screen_off(self):
        self.set_screen(False)

    def set_screen_on(self):
        self.set_screen(True)

    def set_visualizer(self, equalizer_position):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetEqPosition',
            'EqPosition': equalizer_position
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_white_balance(self, white_balance):
        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Device/SetWhiteBalance',
            'RValue': clamp(white_balance[0], 0, 100),
            'GValue': clamp(white_balance[1], 0, 100),
            'BValue': clamp(white_balance[2], 0, 100)
        }))

        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_white_balance_rgb(self, white_balance_r, white_balance_g, white_balance_b):
        self.set_white_balance((white_balance_r, white_balance_g, white_balance_b))

    def validate_connection(self):
        # This won't be possible
        if self.simulated:
            return True

        try:
            # This seems to be a nice low-ping method to test the connection with (in lieu of a ping)
            self.get_all_device_configurations()
        except requests.exceptions.ConnectionError:
            if self.debug:
                print('[x] Connection error')

            return False

        return True

    def __clamp_location(self, xy):
        return clamp(xy[0], 0, self.size - 1), clamp(xy[1], 0, self.size - 1)

    def __error(self, error):
        if self.debug:
            print('[x] Error on request ' + str(self.__counter))
            print(error)

    def __load_counter(self):
        # Just assume it's starting at the beginning if we're simulating
        if self.simulated:
            self.__counter = 1
            return

        response = requests.post(self.__url, '{"Command": "Draw/GetHttpGifId"}')
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
        else:
            self.__counter = int(data['PicId'])
            if self.debug:
                print('[.] Counter loaded and stored: ' + str(self.__counter))

    def __send_buffer(self):

        # Add to the internal counter
        self.__counter = self.__counter + 1

        # Check if we've passed the limit and reset the counter for the animation remotely
        if self.refresh_connection_automatically and self.__counter >= self.__refresh_counter_limit:
            self.__reset_counter()
            self.__counter = 1

        if self.debug:
            print(f'[.] Counter set to {self.__counter}')

        # If it's simulated, we don't need to actually push it to the divoom
        if self.simulated:
            self.__simulator.display(self.__buffer, self.__counter)

            # Simulate this too I suppose
            self.__buffers_send = self.__buffers_send + 1
            return

        # Encode the buffer to base64 encoding
        response = requests.post(self.__url, json.dumps({
            'Command': 'Draw/SendHttpGif',
            'PicNum': 1,
            'PicWidth': self.size,
            'PicOffset': 0,
            'PicID': self.__counter,
            'PicSpeed': 1000,
            'PicData': str(base64.b64encode(bytearray(self.__buffer)).decode())
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
        else:
            self.__buffers_send = self.__buffers_send + 1

            if self.debug:
                print(f'[.] Pushed {self.__buffers_send} buffers')

    def __reset_counter(self):
        if self.debug:
            print(f'[.] Resetting counter remotely')

        # This won't be possible
        if self.simulated:
            return

        response = requests.post(self.__url, json.dumps({
            'Command': 'Draw/ResetHttpGifId'
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
