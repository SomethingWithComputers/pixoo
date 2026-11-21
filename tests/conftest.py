from collections import namedtuple

import pytest
import requests

from pixoo import Pixoo

Call = namedtuple('Call', 'url payload timeout')


class FakeResponse:
    def __init__(self, data=None, status_code=200, content=None):
        self._data = {'error_code': 0} if data is None else data
        self.status_code = status_code
        self.content = b'{}' if content is None else content
        self.text = self.content.decode(errors='replace')

    def json(self):
        if not self.content:
            raise ValueError('No JSON content')
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'HTTP {self.status_code}')


class FakeSession:
    def __init__(self):
        self.calls = []
        self.response = FakeResponse()

    def post(self, url, json=None, timeout=None, **kwargs):
        self.calls.append(Call(url, json, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeSimulator:
    def __init__(self):
        self.frames = []

    def display(self, buffer, counter):
        self.frames.append((list(buffer), counter))


def make_pixoo(size=64, simulated=False):
    """Create a Pixoo instance without network access or a Tk simulator."""
    pixoo = Pixoo.__new__(Pixoo)
    pixoo.ip_address = '127.0.0.1'
    pixoo.size = size
    pixoo.pixel_count = size * size
    pixoo.debug = False
    pixoo.simulated = simulated
    pixoo.refresh_connection_automatically = False
    pixoo.device_name = None
    pixoo.timeout = 5
    pixoo.port = 80
    pixoo.path = '/post'
    pixoo._connected = True
    pixoo._Pixoo__session = FakeSession()
    pixoo._Pixoo__url = 'http://127.0.0.1:80/post'
    pixoo._Pixoo__buffer = [0] * (pixoo.pixel_count * 3)
    pixoo._Pixoo__buffers_sent = 0
    pixoo._Pixoo__counter = 0
    pixoo._Pixoo__simulator = None
    return pixoo


@pytest.fixture
def pixoo():
    return make_pixoo()


@pytest.fixture
def pixoo_factory():
    return make_pixoo

