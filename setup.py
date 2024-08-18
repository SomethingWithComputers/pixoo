#!/usr/bin/python
"""
    Setup.py file for pixoo package
"""
from setuptools import setup

setup(
    name="pixoo",
    version="0.8.0",
    author="Ron Talman",
    description=(
        "A library to easily communicate with the Divoom Pixoo 64",
        "(and hopefully soon more screens that support Wi-Fi)",
    ),
    license="BSD",
    keywords="pixoo",
    url="https://github.com/SomethingWithComputers/pixoo#readme",
    packages=['pixoo'],
    install_requires=[
        'Flask ~= 3.0.3',
        'requests ~= 2.32.3',
        'pillow ~= 10.4.0',
        'python-dotenv ~= 1.0.1'
    ],
)
