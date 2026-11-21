from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING, Any

import requests
from PIL import Image, ImageOps

from ..configurations.simulatorconfiguration import SimulatorConfiguration
from ..constants.colors import Palette
from ..constants.font import retrieve_glyph
from ..enums.imageresamplemode import ImageResampleMode
from ..enums.textscrolldirection import TextScrollDirection
from ..utilities import (
    clamp,
    clamp_color,
    lerp_location,
    minimum_amount_of_steps,
    rgb_to_hex_color,
    round_location,
)

if TYPE_CHECKING:
    from .simulator import Simulator

logger = logging.getLogger(__name__)


class PixooError(Exception):
    """Base exception for Pixoo errors."""


class PixooConnectionError(PixooError):
    """Raised when the device cannot be reached."""


class PixooResponseError(PixooError):
    """Raised when the device returns an error or an invalid response."""


class Pixoo:
    __refresh_counter_limit = 32

    def __init__(
            self,
            ip_address=None,
            size=64,
            debug=False,
            refresh_connection_automatically=True,
            simulated=False,
            simulation_config=None,
            device_name=None,
            timeout=5,
            port=80,
            path='/post',
    ):
        if size not in (16, 32, 64):
            raise ValueError('Invalid screen size in pixels given. Valid options are 16, 32, and 64')

        self.debug = debug
        self.simulated = simulated
        self.refresh_connection_automatically = refresh_connection_automatically
        self.size = size
        self.pixel_count = self.size * self.size
        self.device_name = device_name
        self.timeout = timeout
        self.port = port
        self.path = path if path.startswith('/') else '/' + path

        # Per-instance state; these used to be class attributes.
        self.__session = requests.Session()
        self.__buffer = [0] * (self.pixel_count * 3)
        self.__buffers_sent = 0
        self.__counter = 0
        self.__simulator: Simulator | None = None
        self._connected = False

        self.ip_address = ip_address if ip_address is not None else self.find_local_device_ip()
        self.__url = f'http://{self.ip_address}:{self.port}{self.path}'

        # Prefill the buffer
        self.fill()

        self._connected = self.validate_connection()
        if not self._connected:
            logger.warning('[x] No connection could be made. Verify all settings')
            return

        try:
            self.__load_counter()

            # Reset if needed
            if self.refresh_connection_automatically and self.__counter > self.__refresh_counter_limit:
                self.__reset_counter()
        except PixooError as error:
            logger.warning('[x] Could not initialize the frame counter: %s', error)
            self.__counter = 0

        # We're going to need a simulator
        if self.simulated:
            try:
                from .simulator import Simulator
            except ImportError as error:
                raise ImportError(
                    'The simulator requires tkinter. Install the tkinter package for your Python installation.'
                ) from error

            self.__simulator = Simulator(self, simulation_config or SimulatorConfiguration())

    @property
    def is_connected(self):
        return self._connected

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
                    local_y = index // 3
                    self.draw_pixel((xy[0] + local_x, xy[1] + local_y), rgb)

    def draw_character_at_location_rgb(self, character, x=0, y=0, r=255, g=255, b=255):
        self.draw_character(character, (x, y), (r, g, b))

    def draw_filled_rectangle(self, top_left_xy=(0, 0), bottom_right_xy=(1, 1), rgb=Palette.BLACK):
        for y in range(top_left_xy[1], bottom_right_xy[1] + 1):
            for x in range(top_left_xy[0], bottom_right_xy[0] + 1):
                self.draw_pixel((x, y), rgb)

    def draw_filled_rectangle_from_top_left_to_bottom_right_rgb(
            self,
            top_left_x=0,
            top_left_y=0,
            bottom_right_x=1,
            bottom_right_y=1,
            r=0,
            g=0,
            b=0,
    ):
        self.draw_filled_rectangle((top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (r, g, b))

    def draw_image(
            self,
            image_path_or_object,
            xy=(0, 0),
            image_resample_mode=ImageResampleMode.PIXEL_ART,
            pad_resample=False,
    ):
        image = self.__load_or_copy_image(image_path_or_object)
        width, height = image.size

        # See if it needs to be scaled/resized to fit the display
        if pad_resample:
            image = ImageOps.pad(image, (self.size, self.size), image_resample_mode)
        elif width > self.size or height > self.size:
            image.thumbnail((self.size, self.size), Image.Resampling(image_resample_mode))

        if self.debug:
            logger.debug(
                '[.] Resized image to fit on screen (saving aspect ratio): "%s" (%s, %s) -> (%s, %s)',
                image_path_or_object,
                width,
                height,
                image.size[0],
                image.size[1],
            )

        # Convert the loaded image to RGBA
        rgb_image = image.convert('RGBA')

        # Iterate over all pixels in the image and buffer them
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                self.__draw_image_pixel((x + xy[0], y + xy[1]), rgb_image.getpixel((x, y)))

    def draw_image_at_location(
            self,
            image_path_or_object: str | Image.Image,
            x: int,
            y: int,
            image_resample_mode=ImageResampleMode.PIXEL_ART,
    ):
        self.draw_image(image_path_or_object, (x, y), image_resample_mode)

    def draw_image_frame(
            self,
            image_path_or_object: str | Image.Image,
            xy: tuple[int, int],
            frame: tuple[int, int, int, int] | None = None,
    ):
        image = self.__load_or_copy_image(image_path_or_object)
        frame = frame or (0, 0, image.size[0], image.size[1])

        # Clip the requested frame to the image bounds.
        left = max(0, frame[0])
        top = max(0, frame[1])
        right = min(image.size[0], frame[0] + frame[2])
        bottom = min(image.size[1], frame[1] + frame[3])

        rgb_image = image.convert('RGBA')

        for y in range(top, bottom):
            for x in range(left, right):
                self.__draw_image_pixel(
                    (x - left + xy[0], y - top + xy[1]),
                    rgb_image.getpixel((x, y)),
                )

    def draw_image_frame_at_location(
            self,
            image_path_or_object: str | Image.Image,
            x: int,
            y: int,
            frame_x: int,
            frame_y: int,
            frame_width: int,
            frame_height: int,
    ):
        self.draw_image_frame(
            image_path_or_object,
            (x, y),
            (frame_x, frame_y, frame_width, frame_height),
        )

    def draw_line(self, start_xy, stop_xy, rgb=Palette.WHITE):
        amount_of_steps = minimum_amount_of_steps(start_xy, stop_xy)

        if amount_of_steps == 0:
            self.draw_pixel(round_location(start_xy), rgb)
            return

        line = []
        for step in range(amount_of_steps + 1):
            interpolant = step / amount_of_steps
            line.append(round_location(lerp_location(start_xy, stop_xy, interpolant)))

        for pixel in line:
            self.draw_pixel(pixel, rgb)

    def draw_line_from_start_to_stop_rgb(self, start_x, start_y, stop_x, stop_y, r=255, g=255, b=255):
        self.draw_line((start_x, start_y), (stop_x, stop_y), (r, g, b))

    def draw_pixel(self, xy, rgb):
        # If it's not on the screen, we're not going to bother
        if xy[0] < 0 or xy[0] >= self.size or xy[1] < 0 or xy[1] >= self.size:
            if self.debug:
                limit = self.size - 1
                logger.debug(
                    '[!] Invalid coordinates given: (%s, %s) (maximum coordinates are (%s, %s))',
                    xy[0],
                    xy[1],
                    limit,
                    limit,
                )
            return

        # Calculate the index
        index = xy[0] + (xy[1] * self.size)

        # Color it
        self.draw_pixel_at_index(index, rgb)

    def draw_pixel_at_index(self, index, rgb):
        # Validate the index
        if index < 0 or index >= self.pixel_count:
            if self.debug:
                logger.debug(
                    '[!] Invalid index given: %s (maximum index is %s)',
                    index,
                    self.pixel_count - 1,
                )
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
        rgb = clamp_color(rgb)
        self.__buffer = []
        for _ in range(self.pixel_count):
            self.__buffer.extend(rgb)

    def fill_rgb(self, r, g, b):
        self.fill((r, g, b))

    def find_local_device_ip(self):
        if self.simulated:
            return None

        try:
            response = self.__session.post(
                'https://app.divoom-gz.com/Device/ReturnSameLANDevice',
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            logger.warning('[x] Could not discover devices on the local LAN: %s', error)
            return None

        if not isinstance(data, dict):
            logger.warning('[x] Unexpected device discovery response: %s', data)
            return None

        if data.get('ReturnCode') != 0:
            logger.warning('[x] Device discovery failed: %s', data)
            return None

        devices = data.get('DeviceList') or []
        if self.device_name is not None:
            devices = [device for device in devices if device.get('DeviceName') == self.device_name]

        if not devices:
            logger.warning('[x] No devices found on local LAN')
            return None

        if len(devices) > 1:
            logger.warning(
                '[!] Multiple devices found on local LAN, connecting to the first one '
                '(override this by providing a device_name in the constructor): %s',
                devices[0].get('DeviceName'),
            )

        return devices[0].get('DevicePrivateIP')

    def get_all_device_configurations(self):
        if self.simulated:
            return None

        return self.__send_command('Channel/GetAllConf')

    def get_device_time(self):
        if self.simulated:
            return None

        return self.__send_command('Device/GetDeviceTime')

    def load_image(self, image_path) -> Image.Image:
        with Image.open(image_path) as image:
            return image.copy()

    def play_local_gif(self, file_path):
        if self.simulated:
            return

        self.__send_command('Device/PlayTFGif', FileType=0, FileName=file_path)

    def play_local_gif_directory(self, path):
        if self.simulated:
            return

        self.__send_command('Device/PlayTFGif', FileType=1, FileName=path)

    def play_net_gif(self, gif_file_url):
        if self.simulated:
            return

        self.__send_command('Device/PlayTFGif', FileType=2, FileName=gif_file_url)

    def sound_buzzer(self, active_cycle_time=500, inactive_cycle_time=500, total_time=3000):
        if self.simulated:
            return

        self.__send_command(
            'Device/PlayBuzzer',
            ActiveTimeInCycle=active_cycle_time,
            OffTimeInCycle=inactive_cycle_time,
            PlayTotalTime=total_time,
        )

    def push(self):
        self.__send_buffer()

    def reboot(self):
        if self.simulated:
            return

        self.__send_command('Device/SysReboot')

    def send_text(
            self,
            text,
            xy=(0, 0),
            color=Palette.WHITE,
            identifier=1,
            font=2,
            width=None,
            movement_speed=0,
            direction=TextScrollDirection.LEFT,
    ):
        if self.simulated:
            return

        identifier = int(clamp(int(identifier), 0, 19))
        font = int(clamp(int(font), 0, 7))
        width = self.size if width is None else int(width)
        width = int(clamp(width, 16, self.size)) if self.size >= 16 else width
        movement_speed = max(0, int(movement_speed))
        direction = int(direction)

        if direction not in (0, 1):
            raise ValueError('Text scroll direction must be 0 (left) or 1 (right)')

        self.__send_command(
            'Draw/SendHttpText',
            TextId=identifier,
            x=xy[0],
            y=xy[1],
            dir=direction,
            font=font,
            TextWidth=width,
            speed=movement_speed,
            TextString=text,
            color=rgb_to_hex_color(clamp_color(color)),
        )

    def send_text_at_location_rgb(
            self,
            text,
            x=0,
            y=0,
            r=255,
            g=255,
            b=255,
            identifier=1,
            font=2,
            width=None,
            movement_speed=0,
            direction=TextScrollDirection.LEFT,
    ):
        self.send_text(text, (x, y), (r, g, b), identifier, font, width, movement_speed, direction)

    def set_brightness(self, brightness):
        if self.simulated:
            return

        self.__send_command('Channel/SetBrightness', Brightness=int(clamp(int(brightness), 0, 100)))

    def set_channel(self, channel):
        if self.simulated:
            return

        channel = int(channel)
        if channel < 0 or channel > 4:
            raise ValueError('Channel must be between 0 and 4')

        self.__send_command('Channel/SetIndex', SelectIndex=channel)

    def set_clock(self, clock_id):
        if self.simulated:
            return

        self.__send_command('Channel/SetClockSelectId', ClockId=clock_id)

    def set_face(self, face_id):
        self.set_clock(face_id)

    def set_high_light_mode(self, on=True):
        if self.simulated:
            return

        self.__send_command('Device/SetHighLightMode', Mode=1 if on else 0)

    def set_mirror_mode(self, on=False):
        if self.simulated:
            return

        self.__send_command('Device/SetMirrorMode', Mode=1 if on else 0)

    def set_noise_status(self, on=True):
        if self.simulated:
            return

        self.__send_command('Tools/SetNoiseStatus', NoiseStatus=1 if on else 0)

    def set_score_board(self, blue_score, red_score):
        if self.simulated:
            return

        self.__send_command(
            'Tools/SetScoreBoard',
            BlueScore=int(clamp(int(blue_score), 0, 999)),
            RedScore=int(clamp(int(red_score), 0, 999)),
        )

    def set_screen(self, on=True):
        if self.simulated:
            return

        self.__send_command('Channel/OnOffScreen', OnOff=1 if on else 0)

    def set_screen_off(self):
        self.set_screen(False)

    def set_screen_on(self):
        self.set_screen(True)

    def set_visualizer(self, equalizer_position):
        if self.simulated:
            return

        self.__send_command('Channel/SetEqPosition', EqPosition=equalizer_position)

    def set_white_balance(self, white_balance):
        if self.simulated:
            return

        self.__send_command(
            'Device/SetWhiteBalance',
            RValue=int(clamp(int(white_balance[0]), 0, 100)),
            GValue=int(clamp(int(white_balance[1]), 0, 100)),
            BValue=int(clamp(int(white_balance[2]), 0, 100)),
        )

    def set_white_balance_rgb(self, white_balance_r, white_balance_g, white_balance_b):
        self.set_white_balance((white_balance_r, white_balance_g, white_balance_b))

    def validate_connection(self):
        if self.simulated:
            self._connected = True
            return True

        try:
            # This seems to be a nice low-ping method to test the connection with (in lieu of a ping)
            self.get_all_device_configurations()
        except (PixooError, requests.RequestException, ValueError):
            self._connected = False
            if self.debug:
                logger.debug('[x] Connection error', exc_info=True)

            return False

        self._connected = True
        return True

    def __draw_image_pixel(self, xy, pixel):
        if pixel[3] == 0:
            return

        if xy[0] < 0 or xy[0] >= self.size or xy[1] < 0 or xy[1] >= self.size:
            return

        if pixel[3] == 255:
            self.draw_pixel(xy, pixel[:3])
            return

        # Alpha blend over the current buffer contents.
        index = (xy[0] + (xy[1] * self.size)) * 3
        alpha = pixel[3] / 255
        blended = tuple(
            round(pixel[channel] * alpha + self.__buffer[index + channel] * (1 - alpha))
            for channel in range(3)
        )
        self.draw_pixel(xy, blended)

    def __load_or_copy_image(self, image_path_or_object) -> Image.Image:
        if isinstance(image_path_or_object, Image.Image):
            return image_path_or_object.copy()

        with Image.open(image_path_or_object) as image:
            return image.copy()

    def __send_command(self, command, **parameters) -> dict[str, Any]:
        payload = {'Command': command, **parameters}

        try:
            response = self.__session.post(self.__url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            self._connected = False
            raise PixooConnectionError(f'Request to {self.__url} failed: {error}') from error

        # Some commands (for example Device/SysReboot) may not return a body.
        if not response.content:
            self._connected = True
            return {}

        try:
            data = response.json()
        except ValueError as error:
            raise PixooResponseError(f'Invalid JSON response for {command}: {response.text!r}') from error

        if not isinstance(data, dict):
            raise PixooResponseError(f'Invalid response for {command}: {data!r}')

        if data.get('error_code', 0) != 0:
            raise PixooResponseError(f'{command} failed: {data}')

        self._connected = True
        return data

    def __load_counter(self):
        # Just assume it's starting at the beginning if we're simulating
        if self.simulated:
            self.__counter = 1
            return

        data = self.__send_command('Draw/GetHttpGifId')
        self.__counter = int(data.get('PicId', 0))
        if self.debug:
            logger.debug('[.] Counter loaded and stored: %s', self.__counter)

    def __send_buffer(self):
        # Add to the internal counter
        self.__counter += 1

        # Check if we've passed the limit and reset the counter for the animation remotely
        if self.refresh_connection_automatically and self.__counter > self.__refresh_counter_limit:
            self.__reset_counter()

        if self.debug:
            logger.debug('[.] Counter set to %s', self.__counter)

        # If it's simulated, we don't need to actually push it to the divoom
        if self.simulated:
            if self.__simulator is None:
                raise PixooError('Simulator is not initialized')

            self.__simulator.display(self.__buffer, self.__counter)

            # Simulate this too I suppose
            self.__buffers_sent += 1
            return

        self.__send_command(
            'Draw/SendHttpGif',
            PicNum=1,
            PicWidth=self.size,
            PicOffset=0,
            PicID=self.__counter,
            PicSpeed=1000,
            PicData=str(base64.b64encode(bytearray(self.__buffer)).decode()),
        )

        self.__buffers_sent += 1

        if self.debug:
            logger.debug('[.] Pushed %s buffers', self.__buffers_sent)

    def __reset_counter(self):
        if self.debug:
            logger.debug('[.] Resetting counter remotely')

        if self.simulated:
            self.__counter = 1
            return

        self.__send_command('Draw/ResetHttpGifId')
        self.__counter = 1
