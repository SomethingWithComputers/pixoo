#!/bin/python3
""" Better interaction with request module and pixoo API """
import requests
import pixoo.exceptions as _exceptions


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
