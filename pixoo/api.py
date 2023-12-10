#!/bin/python3
""" Better interaction with request module and pixoo API """
import requests
import pixoo.exceptions as _exceptions


def _snake_to_camel(string):
    """ Convert string from snake_case to camelCase """
    return "".join(word.title() for word in string.split("_"))


class ApiResponse:
    """ Automatic check of Pixoo API response """
    def __init__(self, api_response: requests.models.Response):
        self.__data = self.__validate_response(api_response)

    def __validate_response(self, api_response):
        response = api_response.json()
        if response["ReturnCode"] != 0:
            raise _exceptions.InvalidApiResponse(
                f"API Return code is not 0. Return Code: {response['ReturnCode']} ({response['ReturnMessage']})")  # pylint: disable=line-too-long
        return response

    @property
    def data(self):
        """ Return API response (just json data) """
        return self.__data


def _get_cmd_response(api_response: requests.models.Response):
    """ Validate response of Pixoo API command """
    response = api_response.json()
    if "error_code" in response:
        if response["error_code"] != 0:
            raise _exceptions.InvalidApiResponse(
                f"Command error code is not 0. Error Code: {response['error_code']} ({response['error_message']})")  # pylint: disable=line-too-long
    return response


class PixooBaseApi:
    # pylint: disable=too-few-public-methods
    """ Talk with Pixoo API """
    def __init__(self, address: str):
        self.__address = address

    def send_command(self, command: str, timeout=60, **arguments):
        """ Send command to Pixoo API """
        # Prepare data to send. Command is the first item in the dict
        data = {"Command": command}
        # Send arguments taken in snake_case to camelCase
        for arg, value in arguments.items():
            data.update({_snake_to_camel(arg): value})
        response = requests.post(
            f"http://{self.__address}/post", json=data, timeout=timeout)
        return _get_cmd_response(response)
