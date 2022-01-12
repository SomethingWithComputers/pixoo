# Pixoo

A library to easily communicate with the Divoom Pixoo 64 (and hopefully soon more screens that support Wi-Fi)

Tested on a Pixoo 64.

## Installation

Simply install the required dependencies via PIP. Navigate to the directory where you installed this library. Then
execute:

```
pip install -r requirements.txt
```

Install the requirements.txt via pip install

## Getting started

Create an interface with your device as such (of course use your own local IP-address):

```
pixoo = Pixoo('192.168.1.137')
```

For now, the easiest way to learn how to use this library is to check the `examples.py`. I'll be adding examples to this
page over time as well, once the project matures a bit more.

**NOTE:** Be sure to call `push()` after performing all your draw actions, to push the internal buffer to the screen. *
Try to not call this method more than once per second if you don't want the device to stop responding!*

## Known bugs

#### Previous buffer/image is still partially visible

Unfortunately, the Divoom Pixoo 64 doesn't seem quite ready for prime time- *yet*. There are some known buffer issues
that can cause issues, basically meaning that parts of the previous image are still displayed even though a newer image
has been pushed to the display. I'm sure this will be fixed in the future though, the dev team seems to be working hard!

#### After updating the screen +/- 300 times the display stops responding

This seems to be an internal bug with the current firmware. I'll update the code once a better way to push a buffer to
the screen becomes available.

#### TextScrollDirection.RIGHT seems to invert the string

.. and some other issues. Seems like for now, text can only really be scrolling left with most fonts. This will likely (
hopefully?) be fixed by the dev team in the future.