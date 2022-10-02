from pixoo import Channel, ImageResampleMode, Pixoo

'''
Create a connection to a Pixoo

First argument is its IP address (required)
The second argument is the display size (optional, default 64)
The third argument is the 'debug mode' (optional, default False), which enables logging of important actions
'''
pixoo = Pixoo('192.168.50.214', 64, True)

# The following are all 'drawing' methods.
# Afterwards, be sure to call `pixoo.push()` to send the internal buffer to the connected display
'''
Fill the display with the given color
'''
pixoo.fill((255, 0, 68))
# or
pixoo.fill_rgb(255, 0, 68)

'''
Draw a filled rectangle from top-left to bottom-right
'''
pixoo.draw_filled_rectangle((1, 1), (62, 62), (255, 99, 0))
# or
pixoo.draw_filled_rectangle_from_top_left_to_bottom_right_rgb(1, 1, 62, 62, 255, 99, 0)

'''
Draw a pixel at a location to a given color (starting top left)
'''
pixoo.draw_pixel((0, 0), (255, 255, 255))  # Sets the top left pixel to full white
# or
pixoo.draw_pixel_at_location_rgb(0, 0, 255, 255, 255)

'''
Draw a pixel at the given index (each pixel has its own index based on the position on the display, starting top left
'''
pixoo.draw_pixel_at_index(127, (255, 255, 255))  # Set the pixel at (63, 1) to full white
# or
pixoo.draw_pixel_at_index_rgb(127, 255, 255, 255)

'''
Draw a string of text at a given position with a given color using the PICO-8 font
The font's glyphs are at a maximum 3 pixels wide and 5 pixels high. We're using 4 pixels per glyph for nicer kerning
Supported characters so far are:
```
0123456789
abcdefghijklmnopqrstuvwxyz
ABCDEFGHIJKLMNOPQRSTUVWXYZ
!'()+,-<=>?[]^_:;./{|}~$@%
```
This will draw text to the buffer (so call `push()`) and it's not the same as `send_text` (and therefore less buggy)
'''
pixoo.draw_text('Hello there..', (0, 0), (0, 255, 0))
pixoo.draw_text('GENERAL KENOBI', (0, 6), (255, 0, 0))
# or
pixoo.draw_text_at_location_rgb('Neat', 0, 6, 255, 255, 0)

'''
Load and add an image to the buffer.

If the image is too large (e.g. larger than 64x64 pixels) it'll be resized to fit the display, keeping aspect ratio
The image can be resized fit for pixel art or smooth: ImageResampleMode.PIXEL_ART or ImageResampleMode.SMOOTH

If a location is provided, the image might be cut off the sides of the display based on the location.
Locations can be larger than the screen size (though the image would be off-screen) or contain coordinates < 0.
'''
pixoo.draw_image('tiny.png')  # Adds image at path 'tiny.png' at default location (0, 0)
# or
pixoo.draw_image('tiny.png', (12, 16))  # Adds image at path 'tiny.png' at location (12, 16)
# or
pixoo.draw_image('tiny.png', (-10, -14), ImageResampleMode.SMOOTH)  # Resizes the image but uses anti-aliasing
# or
pixoo.draw_image_at_location('tiny.png', 10, 10)  # Alternative way of providing coordinates

'''
Draw a line from point start to stop with a given color
'''
pixoo.draw_line((10, 12), (32, 54), (90, 12, 255))
# or
pixoo.draw_line_from_start_to_stop_rgb(10, 12, 32, 54, 90, 12, 255)

'''
The push methods pushes the buffer to the screen, needs to be called after you're done with all drawing-type methods
'''
pixoo.push()

# The following are all 'device' methods.
'''
Set the current Channel on the display

Use the Channel enum from the library to help a bit. Available channels are: FACES, CLOUD, VISUALIZER, and CUSTOM
'''
pixoo.set_channel(Channel.FACES)

'''
After setting the channel to FACES (ClockFACES I assume?) you can select a clock like this

The clock id is a number that corresponds to the installed clocks on your device
'''
pixoo.set_clock(0)

'''
Turn the screen on/off

The screen still renders internally when off, but nothing will be shown on the display
'''
pixoo.set_screen_off()
pixoo.set_screen_on()
pixoo.set_screen(False)

'''
After setting the channel to VISUALIZER you can select a audio visualizer like this

The visualizer id is a number that corresponds to the installed visualizers on your device
'''
pixoo.set_visualizer(0)

'''
Set the brightness of the display

The brightness needs to be an integer between inclusive 0 and 100
'''
pixoo.set_brightness(100)

'''
Send text to the display using (currently seemingly in alpha) text functionality
def send_text(self, text, xy=(0, 0), color=(255, 255, 255), identifier=1, font=2, width=64,
              movement_speed=0,
              direction=TextScrollDirection.RIGHT):
The first argument is the string to be displayed (required)
The second argument is the position to place the string (optional, default (0, 0))
the third argument is the color of the text (optional, default (255, 255, 255))
The fourth is the text identifier. Use this to update existing text on the display (optional, default 1, has to be
between 0 and 20)
The fifth is the font identifier (optional, default 2, has to be between 0 and 7 but support seems limited for some fonts)
The sixth argument is the width of the "textbox" (optional, default 64)
The seventh argument is the movement speed of the text in case it doesn't fit the "textbox" (optional, default 0)
    **NOTE:** Currently there seems to be no way to stop the movement
The eight and final argument is the movement direction of the text (optional, default TextScrollDirection.LEFT)
    **NOTE:** Currently TextScrollDirection.RIGHT seems broken on the display

NOTE: Currently this is **not** a drawing method, so it'll add the text over whatever is already on screen
'''
# Send text after pushing all your other data, because it'll otherwise be overwritten if it's not animated
pixoo.send_text('Hello there', (0, 0), (10, 255, 0), 1, 6)
pixoo.send_text('GENERAL KENOBI', (0, 15), (255, 0, 0), 2, 6)
