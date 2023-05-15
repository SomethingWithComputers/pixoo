#!/usr/bin/python3
""" Discovers pixoo devices in your local network and their IPs.

This module is used to find pixoo devices in your local network to later use
them by the Pixoo library
"""
import requests as _requests
from pixoo.api import ApiResponse as _ApiResponse
import pixoo.exceptions as _exceptions


def get_pixoo_devices():
    """ Get Pixoo devices detected in your local network """
    # This method is using the 'Find device' documentation from:
    #   http://doc.divoom-gz.com/web/#/12?page_id=336
    response = _ApiResponse(_requests.post(
        "https://app.divoom-gz.com/Device/ReturnSameLANDevice",
        timeout=100,
    ))
    device_list = response.data["DeviceList"]
    if len(device_list) == 0:
        raise _exceptions.NoPixooDevicesFound
    return device_list


def show_pixoo_devices():
    """ Show information of pixoo devices in local network """
    pixoo_devices = get_pixoo_devices()
    print(f" Pixo Devices ({len(pixoo_devices)})".center(40, "-"))
    for index, pixoo_device in enumerate(pixoo_devices):
        dev_name = pixoo_device["DeviceName"]
        dev_ip = pixoo_device["DevicePrivateIP"]
        print(f"  {index + 1}.- {dev_name} (IP: {dev_ip})")
    print("-" * 40)
