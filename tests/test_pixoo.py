import requests
from conftest import FakeResponse
from PIL import Image

from pixoo import Channel, Pixoo, TextScrollDirection
from pixoo.utilities import rgb_to_hex_color


def pixel_at(pixoo, x, y):
    index = (x + y * pixoo.size) * 3
    return tuple(pixoo._Pixoo__buffer[index:index + 3])


def last_payload(pixoo):
    return pixoo._Pixoo__session.calls[-1].payload


def test_invalid_size_raises():
    try:
        Pixoo(size=10)
    except ValueError as error:
        assert '16, 32, and 64' in str(error)
    else:
        raise AssertionError('Expected ValueError')


def test_draw_line_draws_final_endpoint(pixoo):
    pixoo.fill((0, 0, 0))
    pixoo.draw_line((0, 0), (2, 0), (255, 0, 0))

    assert pixel_at(pixoo, 0, 0) == (255, 0, 0)
    assert pixel_at(pixoo, 1, 0) == (255, 0, 0)
    assert pixel_at(pixoo, 2, 0) == (255, 0, 0)


def test_draw_line_zero_length_draws_one_pixel(pixoo):
    pixoo.fill((0, 0, 0))
    pixoo.draw_line((5, 5), (5, 5), (255, 0, 0))

    assert pixel_at(pixoo, 5, 5) == (255, 0, 0)


def test_draw_image_frame_defaults_to_full_image(pixoo):
    image = Image.new('RGB', (10, 10), (255, 0, 0))
    pixoo.fill((0, 0, 0))
    pixoo.draw_image_frame(image, (0, 0))

    assert pixel_at(pixoo, 0, 0) == (255, 0, 0)
    assert pixel_at(pixoo, 9, 9) == (255, 0, 0)


def test_draw_image_frame_clips_to_image_bounds(pixoo):
    image = Image.new('RGB', (4, 4), (255, 0, 0))
    for y in range(4):
        for x in range(2, 4):
            image.putpixel((x, y), (0, 0, 255))

    pixoo.fill((0, 0, 0))
    pixoo.draw_image_frame(image, (0, 0), (2, 0, 2, 4))

    assert pixel_at(pixoo, 0, 0) == (0, 0, 255)
    assert pixel_at(pixoo, 2, 0) == (0, 0, 0)


def test_draw_image_blends_alpha(pixoo):
    pixoo.fill((100, 0, 0))
    image = Image.new('RGBA', (2, 2), (0, 0, 255, 128))
    pixoo.draw_image(image)

    assert pixel_at(pixoo, 0, 0) == (50, 0, 128)


def test_draw_image_pad_resample_pads_small_images(pixoo):
    image = Image.new('RGB', (4, 2), (255, 255, 255))
    pixoo.fill((255, 0, 0))
    pixoo.draw_image(image, pad_resample=True)

    assert pixel_at(pixoo, 0, 0) == (0, 0, 0)
    assert pixel_at(pixoo, 31, 31) == (255, 255, 255)


def test_rgb_to_hex_color_clamps_values():
    assert rgb_to_hex_color((255, 0, 0)) == '#FF0000'
    assert rgb_to_hex_color((256, 0, 0)) == '#FF0000'
    assert rgb_to_hex_color((-1, 256, 0)) == '#00FF00'


def test_on_off_payloads_are_integers(pixoo):
    cases = [
        (pixoo.set_screen, 'OnOff'),
        (pixoo.set_high_light_mode, 'Mode'),
        (pixoo.set_mirror_mode, 'Mode'),
        (pixoo.set_noise_status, 'NoiseStatus'),
    ]

    for method, key in cases:
        method(True)
        value = last_payload(pixoo)[key]
        assert value == 1
        assert type(value) is int

        method(False)
        value = last_payload(pixoo)[key]
        assert value == 0
        assert type(value) is int


def test_non_boolean_payloads_remain_numeric(pixoo):
    pixoo.send_text('hello', width=32, identifier=4, font=6, direction=TextScrollDirection.RIGHT)
    text_payload = last_payload(pixoo)
    assert text_payload['TextId'] == 4
    assert text_payload['font'] == 6
    assert text_payload['dir'] == 1
    assert type(text_payload['dir']) is int
    assert text_payload['TextWidth'] == 32
    assert text_payload['color'] == '#FFFFFF'

    pixoo.play_net_gif('http://example.com/test.gif')
    assert last_payload(pixoo)['FileType'] == 2

    pixoo.set_channel(Channel.BLACK_SCREEN)
    assert last_payload(pixoo)['SelectIndex'] == 4

    pixoo.set_brightness(50)
    assert last_payload(pixoo)['Brightness'] == 50

    pixoo.set_score_board(10, 20)
    score_payload = last_payload(pixoo)
    assert score_payload['BlueScore'] == 10
    assert score_payload['RedScore'] == 20

    pixoo.set_white_balance((10, 20, 30))
    white_balance_payload = last_payload(pixoo)
    assert white_balance_payload['RValue'] == 10
    assert white_balance_payload['GValue'] == 20
    assert white_balance_payload['BValue'] == 30


def test_push_payload_uses_size_and_numeric_fields(pixoo):
    pixoo.push()
    payload = last_payload(pixoo)

    assert payload['Command'] == 'Draw/SendHttpGif'
    assert payload['PicNum'] == 1
    assert payload['PicWidth'] == 64
    assert payload['PicOffset'] == 0
    assert payload['PicID'] == 1
    assert payload['PicSpeed'] == 1000
    assert isinstance(payload['PicData'], str)


def test_send_text_default_width_uses_display_size(pixoo_factory):
    pixoo = pixoo_factory(16)
    pixoo.send_text('x')

    assert last_payload(pixoo)['TextWidth'] == 16


def test_reboot_does_nothing_in_simulator_mode(pixoo_factory):
    pixoo = pixoo_factory(simulated=True)
    pixoo.reboot()

    assert pixoo._Pixoo__session.calls == []


def test_empty_response_body_is_accepted(pixoo):
    pixoo._Pixoo__session.response = FakeResponse(content=b'')
    pixoo.reboot()

    assert pixoo.is_connected is True


def test_request_uses_json_payload_and_timeout(pixoo):
    pixoo.set_brightness(50)
    call = pixoo._Pixoo__session.calls[-1]

    assert call.payload['Command'] == 'Channel/SetBrightness'
    assert call.timeout == 5


def test_validate_connection_returns_false_on_device_error(pixoo):
    pixoo._Pixoo__session.response = FakeResponse({'error_code': 1})

    assert pixoo.validate_connection() is False
    assert pixoo.is_connected is False


def test_validate_connection_returns_false_on_request_error(pixoo):
    pixoo._Pixoo__session.response = requests.ConnectionError('offline')

    assert pixoo.validate_connection() is False
    assert pixoo.is_connected is False


def test_counter_reset_happens_before_send(pixoo):
    pixoo.refresh_connection_automatically = True
    pixoo._Pixoo__counter = 32

    pixoo.push()

    commands = [call.payload['Command'] for call in pixoo._Pixoo__session.calls]
    assert commands == ['Draw/ResetHttpGifId', 'Draw/SendHttpGif']
    assert pixoo._Pixoo__session.calls[-1].payload['PicID'] == 1


def test_find_local_device_ip_filters_by_device_name(pixoo):
    pixoo.device_name = 'B'
    pixoo._Pixoo__session.response = FakeResponse({
        'ReturnCode': 0,
        'DeviceList': [
            {'DeviceName': 'A', 'DevicePrivateIP': '192.168.1.10'},
            {'DeviceName': 'B', 'DevicePrivateIP': '192.168.1.20'},
        ],
    })

    assert pixoo.find_local_device_ip() == '192.168.1.20'
    assert pixoo._Pixoo__session.calls[-1].url.endswith('/Device/ReturnSameLANDevice')


def test_find_local_device_ip_returns_none_on_error(pixoo):
    pixoo._Pixoo__session.response = FakeResponse({'ReturnCode': 1})

    assert pixoo.find_local_device_ip() is None


def test_simulated_push_uses_simulator(pixoo_factory):
    from conftest import FakeSimulator

    pixoo = pixoo_factory(simulated=True)
    pixoo._Pixoo__simulator = FakeSimulator()

    pixoo.push()

    assert len(pixoo._Pixoo__simulator.frames) == 1
    assert pixoo._Pixoo__simulator.frames[0][1] == 1
    assert pixoo._Pixoo__session.calls == []
