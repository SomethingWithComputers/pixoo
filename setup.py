#!/usr/bin/python
"""
    Setup.py file for pixoo package
"""
from setuptools import setup

setup(
    name="pixoo",
    version="0.9.0",
    author="Ron Talman",
    description="A library to easily communicate with the Divoom Pixoo 64",
    license="CC BY-NC-SA",
    keywords="pixoo, divoom, pixoo64",
    url="https://github.com/SomethingWithComputers/pixoo#readme",
    packages=['pixoo'],
    project_urls={
        "Issue Tracker": "https://github.com/SomethingWithComputers/pixoo/issues",
        "Source": "https://github.com/SomethingWithComputers/pixoo"
    },
    install_requires=[
        'Flask ~= 3.0.3',
        'requests ~= 2.32.3',
        'pillow ~= 10.4.0'
    ],
    python_requires='>=3.10',
    include_package_data=True
)
