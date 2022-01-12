import base64
import json
from enum import IntEnum

from PIL import Image
import requests


def clamp(value, minimum=0, maximum=255):
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum

    return value


def clamp_color(rgb):
    return clamp(rgb[0]), clamp(rgb[1]), clamp(rgb[2])


def rgb_to_hex_color(rgb):
    return f'#{rgb[0]:0>2X}{rgb[1]:0>2X}{rgb[2]:0>2X}'


class Channel(IntEnum):
    FACES = 0
    CLOUD = 1
    VISUALIZER = 2
    CUSTOM = 3


class ImageResampleMode(IntEnum):
    PIXEL_ART = Image.NEAREST
    SMOOTH = Image.ANTIALIAS


class TextScrollDirection(IntEnum):
    LEFT = 0
    RIGHT = 1


class Pixoo:
    __buffer = []
    __buffers_send = 0
    __counter = 0

    def __init__(self, address, size=64, debug=False):
        assert size in [16, 32, 64], 'Invalid screen size in pixels given. Valid options are 16, 32, and 64'

        self.address = address
        self.debug = debug
        self.size = size

        # Total number of pixels
        self.pixel_count = self.size * self.size

        # Generate URL
        self.__url = 'http://{0}/post'.format(address)

        # Prefill the buffer
        self.fill()

        # Retrieve the counter
        self.__load_counter()

    def add_image(self, image_path, xy=(0, 0), image_resample_mode=ImageResampleMode.PIXEL_ART):
        image = Image.open(image_path)
        size = image.size
        width = size[0]
        height = size[1]

        # See if it needs to be scaled/resized to fit the display
        if width > self.size or height > self.size:
            image.thumbnail((self.size, self.size), image_resample_mode)

            if self.debug:
                print(
                    f'[.] Resized image to fit on screen (saving aspect ratio): "{image_location}" ({width}, {height}) -> ({image.size[0]}, {image.size[1]})')

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

                self.set_pixel((placed_x, placed_y), rgb_image.getpixel(location))

    def add_image_at_location(self, image_path, x, y, image_resample_mode=ImageResampleMode.PIXEL_ART):
        self.add_image(image_path, (x, y), image_resample_mode)

    def send_text(self, text, xy=(0, 0), color=(255, 255, 255), identifier=1, font=2, width=64,
                  movement_speed=0,
                  direction=TextScrollDirection.LEFT):

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

    def fill(self, rgb=(0, 0, 0)):
        self.__buffer = []
        rgb = clamp_color(rgb)
        for index in range(self.pixel_count):
            self.__buffer.extend(rgb)

    def fill_rgb(self, r, g, b):
        self.fill((r, g, b))

    def push(self):
        self.__send_buffer()

    def set_brightness(self, brightness):
        brightness = clamp(brightness, 0, 100)
        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetBrightness',
            'Brightness': brightness
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_channel(self, channel):
        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetIndex',
            'SelectIndex': int(channel)
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_clock(self, clock_id):
        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetClockSelectId',
            'ClockId': clock_id
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def set_face(self, face_id):
        self.set_clock(face_id)

    def set_pixel(self, xy, rgb):
        assert (0 <= xy[0] < self.size and 0 <= xy[
            1] < self.size), f'Invalid coordinates given: ({xy[0]}, {xy[1]}) (maximum coordinates are ({self.size - 1}, {self.size - 1})'

        # Clamp the location to the screen
        xy = self.__clamp_location(xy)

        index = xy[0] + (xy[1] * self.size)
        self.set_pixel_at_index(index, rgb)

    def set_pixel_at_index(self, index, rgb):
        assert index < self.pixel_count, f'Invalid index given: {index} (maximum index is {self.pixel_count - 1})'

        # Clamp the color, just to be safe
        rgb = clamp_color(rgb)

        # Move to place in array
        index = index * 3

        self.__buffer[index] = rgb[0]
        self.__buffer[index + 1] = rgb[1]
        self.__buffer[index + 2] = rgb[2]

    def set_pixel_at_index_rgb(self, index, r, g, b):
        self.set_pixel_at_index(index, (r, g, b))

    def set_pixel_at_location_rgb(self, x, y, r, g, b):
        self.set_pixel((x, y), (r, g, b))

    def set_visualizer(self, equalizer_position):
        response = requests.post(self.__url, json.dumps({
            'Command': 'Channel/SetEqPosition',
            'EqPosition': equalizer_position
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)

    def __clamp_location(self, xy):
        return clamp(xy[0], 0, self.size - 1), clamp(xy[1], 0, self.size - 1)

    def __error(self, error):
        if self.debug:
            print('[x] Error on request ' + str(self.__counter))
            print(error)

    def __load_counter(self):
        response = requests.post(self.__url, '{"Command": "Draw/GetHttpGifId"}')
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
        else:
            self.__counter = int(data['PicId'])
            if self.debug:
                print('[.] Counter loaded and stored: ' + str(self.__counter))

    def __send_buffer(self):
        # Encode the buffer to base64 encoding
        base64_bytes = base64.b64encode(bytearray(self.__buffer))

        # Add to the internal counter
        self.__counter = self.__counter + 1

        if self.debug:
            print(f'[.] Counter set to {self.__counter}')

        response = requests.post(self.__url, json.dumps({
            'Command': 'Draw/SendHttpGif',
            'PicNum': 1,
            'PicWidth': self.size,
            'PicOffset': 0,
            'PicID': self.__counter,
            'PicSpeed': 1000,
            'PicData': str(base64_bytes.decode())
        }))
        data = response.json()
        if data['error_code'] != 0:
            self.__error(data)
        else:
            self.__buffers_send = self.__buffers_send + 1

            if self.debug:
                print(f'[.] Pushed {self.__buffers_send} buffers')


__all__ = (Channel, ImageResampleMode, Pixoo, TextScrollDirection)
