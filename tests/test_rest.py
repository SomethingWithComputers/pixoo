from conftest import FakeResponse

from pixoo import PixooConfiguration, PixooREST, RESTConfiguration


def make_client(pixoo):
    rest = PixooREST(
        pixoo=pixoo,
        rest_configuration=RESTConfiguration(debug=False, name='test-pixoo'),
        run_server=False,
    )
    return rest.rest.test_client()


def test_push_endpoint(pixoo):
    client = make_client(pixoo)

    response = client.post('/push')

    assert response.status_code == 200
    assert response.get_json() == {'success': True}
    assert pixoo._Pixoo__session.calls[-1].payload['Command'] == 'Draw/SendHttpGif'


def test_set_brightness_endpoint(pixoo):
    client = make_client(pixoo)

    response = client.post('/setbrightness/55')

    assert response.status_code == 200
    assert pixoo._Pixoo__session.calls[-1].payload['Brightness'] == 55


def test_on_off_endpoints_send_integers(pixoo):
    client = make_client(pixoo)

    cases = [
        ('/setscreen/1', 'OnOff', 1),
        ('/setscreen/0', 'OnOff', 0),
        ('/sethighlight/1', 'Mode', 1),
        ('/sethighlight/0', 'Mode', 0),
        ('/setmirror/1', 'Mode', 1),
        ('/setmirror/0', 'Mode', 0),
        ('/setnoise/1', 'NoiseStatus', 1),
        ('/setnoise/0', 'NoiseStatus', 0),
    ]

    for url, key, expected in cases:
        response = client.post(url)
        assert response.status_code == 200
        value = pixoo._Pixoo__session.calls[-1].payload[key]
        assert value == expected
        assert type(value) is int


def test_device_configuration_endpoint(pixoo):
    pixoo._Pixoo__session.response = FakeResponse({'error_code': 0, 'Brightness': 42})
    client = make_client(pixoo)

    response = client.post('/deviceconfigurations')

    assert response.status_code == 200
    assert response.get_json()['Brightness'] == 42


def test_device_time_endpoint(pixoo):
    pixoo._Pixoo__session.response = FakeResponse({
        'error_code': 0,
        'UTCTime': 1647200428,
        'LocalTime': '2022-03-14 03:40:28',
    })
    client = make_client(pixoo)

    response = client.post('/devicetime')

    assert response.status_code == 200
    assert response.get_json()['UTCTime'] == 1647200428


def test_white_balance_and_scoreboard_endpoints(pixoo):
    client = make_client(pixoo)

    response = client.post('/setwhitebalance/10/20/30')
    assert response.status_code == 200
    payload = pixoo._Pixoo__session.calls[-1].payload
    assert (payload['RValue'], payload['GValue'], payload['BValue']) == (10, 20, 30)

    response = client.post('/setscoreboard/100/79')
    assert response.status_code == 200
    payload = pixoo._Pixoo__session.calls[-1].payload
    assert (payload['BlueScore'], payload['RedScore']) == (100, 79)


def test_channel_and_text_endpoints(pixoo):
    client = make_client(pixoo)

    response = client.post('/setchannel/2')
    assert response.status_code == 200
    assert pixoo._Pixoo__session.calls[-1].payload['SelectIndex'] == 2

    response = client.post('/sendtext/hello/0/0/255/255/255/1/2/32/0/0')
    assert response.status_code == 200
    payload = pixoo._Pixoo__session.calls[-1].payload
    assert payload['Command'] == 'Draw/SendHttpText'
    assert payload['TextWidth'] == 32
    assert payload['dir'] == 0


def test_rest_passes_pixoo_configuration(monkeypatch):
    import pixoo.objects.pixoorest as pixoorest_module

    captured = {}

    class FakePixoo:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(pixoorest_module, 'Pixoo', FakePixoo)

    PixooREST(
        pixoo_configuration=PixooConfiguration(
            ip_address='192.168.1.50',
            size=32,
            debug=True,
            simulated=True,
        ),
        rest_configuration=RESTConfiguration(debug=False, name='test-config'),
        run_server=False,
    )

    assert captured['ip_address'] == '192.168.1.50'
    assert captured['size'] == 32
    assert captured['debug'] is True
    assert captured['simulated'] is True


def test_rest_returns_400_on_invalid_input(pixoo):
    client = make_client(pixoo)

    response = client.post('/setchannel/9')

    assert response.status_code == 400
    body = response.get_json()
    assert body['success'] is False
    assert 'Channel' in body['error']


def test_rest_returns_502_on_device_error(pixoo):
    pixoo._Pixoo__session.response = FakeResponse({'error_code': 1})
    client = make_client(pixoo)

    response = client.post('/setbrightness/50')

    assert response.status_code == 502
    body = response.get_json()
    assert body['success'] is False
    assert 'error' in body
