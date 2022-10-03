import tkinter

from PIL import ImageTk, Image, ImageDraw

from ._colors import Palette


class SimulatorConfig:
    def __init__(self, scale=4):
        self.scale = scale


class Simulator:
    __config = None
    __image_container = None
    __image_size = (64, 64)
    __root = None
    __screen_size = (64, 64)
    __window = None

    def __init__(self, pixoo, config):
        self.__config = config
        scale = self.__config.scale
        self.__image_size = (pixoo.size * scale, pixoo.size * scale)
        self.__root = tkinter.Tk()
        self.__root.title('Pixoo Simulator')
        self.__root.geometry('{0}x{1}'.format(self.__image_size[0], self.__image_size[1]))
        self.__root.attributes('-topmost', True)

        self.__canvas = tkinter.Canvas(self.__root, height=self.__image_size[1], width=self.__image_size[0])
        self.__canvas.pack()

        # Scale it up to something useful
        image = Image.new('RGB', (pixoo.size, pixoo.size), color='red')

        # Create somewhat of a loading screen
        draw = ImageDraw.Draw(image)
        x = 12
        y = 14
        draw.text((x, y), 'waiting', fill=Palette.WHITE)
        draw.text((x + 11, y + 12), 'for', fill=Palette.WHITE)
        draw.text((x + 2, y + 24), 'buffer', fill=Palette.WHITE)

        # Scale it up and convert it to something useful
        image = self.__prepare_image(image)

        # Place the image on the screen
        self.__image_container = self.__canvas.create_image(self.__image_size[0] / 2, self.__image_size[1] / 2,
                                                            image=image)

        # Display the loading screen
        self.__root.update()

    def display(self, buffer, counter):
        # Convert our buffer to a nice image
        image = Image.frombytes('RGB', self.__screen_size, bytes(buffer), 'raw')

        # Scale it up and convert it to something useful
        image = self.__prepare_image(image)

        # Update the image that's already on screen
        self.__canvas.itemconfig(self.__image_container, image=image)

        # Show it
        self.__root.update()

    def __prepare_image(self, image):
        image = image.resize(self.__image_size, Image.NEAREST)
        return ImageTk.PhotoImage(image)


__all__ = (Simulator, SimulatorConfig)
