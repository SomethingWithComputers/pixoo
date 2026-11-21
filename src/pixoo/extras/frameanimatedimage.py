from ..objects.pixoo import Pixoo


class FrameAnimatedImage:
    def __init__(self, pixoo: Pixoo, image_path, frame_width, frame_height):
        self.pixoo = pixoo
        self.frame_height = frame_height
        self.frame_number = 0
        self.frame_width = frame_width

        self.image = self.pixoo.load_image(image_path)
        self.number_of_frames = int(self.image.size[0] / self.frame_width)

    def draw_current_frame(self, xy: tuple[int, int]):
        self.draw_frame_number(xy, self.frame_number)

    def draw_frame_number(self, xy: tuple[int, int], frame_number: int):
        self.frame_number = frame_number
        self.pixoo.draw_image_frame(
            self.image,
            xy,
            (
                self.frame_number * self.frame_width,
                0,
                self.frame_width,
                self.frame_height
            )
        )

    def move_to_next_frame(self):
        self.frame_number = (self.frame_number + 1) % self.number_of_frames
