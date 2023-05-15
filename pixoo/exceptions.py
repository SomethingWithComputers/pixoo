#!/binpython3
""" Pixoo package exceptions """


class InvalidApiResponse(RuntimeError):
    """ Raise this exception when return code is not valid from Pixoo API """


class NoPixooDevicesFound(RuntimeError):
    """ No pixoo devices found in local network """


class MoreThanOnePixooFound(RuntimeError):
    """ More than one pixoo device found in netwoork """
