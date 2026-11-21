class PixooConfiguration:
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
        self.ip_address = ip_address
        self.size = size
        self.debug = debug
        self.refresh_connection_automatically = refresh_connection_automatically
        self.simulated = simulated
        self.simulation_config = simulation_config
        self.device_name = device_name
        self.timeout = timeout
        self.port = port
        self.path = path
