from flask import Flask, jsonify

from .. import Pixoo, PixooConfiguration, RESTConfiguration, TextScrollDirection


class PixooREST:
    def __init__(self, pixoo_configuration=PixooConfiguration(), rest_configuration=RESTConfiguration()):
        self.pixoo = Pixoo(pixoo_configuration.ip_address)

        self.rest = Flask(rest_configuration.name)
        self.rest.add_url_rule('/clear/<int:r>/<int:g>/<int:b>', 'clear', view_func=self.clear_rgb,
                               methods=['GET', 'POST'])
        self.rest.add_url_rule('/drawcharacter/<string:character>/<int:x>/<int:y>/<int:r>/<int:g>/<int:b>',
                               'draw_character', view_func=self.draw_character_at_location_rgb,
                               methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/drawfilledrectangle/<int:top_left_x>/<int:top_left_y>/<int:bottom_right_x>/<int:bottom_right_y>/'
            '<int:r>/<int:g>/<int:b>',
            'draw_filled_rectangle', view_func=self.draw_filled_rectangle_from_top_left_to_bottom_right_rgb,
            methods=['GET', 'POST'])
        # MARKTWAIN - Find a way to draw image, possibly with hex encoding?
        self.rest.add_url_rule(
            '/drawline/<int:start_x>/<int:start_y>/<int:stop_x>/<int:stop_y>/<int:r>/<int:g>/<int:b>',
            'draw_line', view_func=self.draw_line_from_start_to_stop_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/drawpixel/<int:index>/<int:r>/<int:g>/<int:b>',
            'draw_pixel_at_index', view_func=self.draw_pixel_at_index_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/drawpixel/<int:x>/<int:y>/<int:r>/<int:g>/<int:b>',
            'draw_pixel_at_location', view_func=self.draw_pixel_at_location_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/drawtext/<string:text>/<int:x>/<int:y>/<int:r>/<int:g>/<int:b>',
            'draw_text_at_location', view_func=self.draw_text_at_location_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/deviceconfigurations',
            'device_configuration', view_func=self.get_all_device_configurations,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/devicetime',
            'device_time', view_func=self.get_device_time,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/fill/<int:r>/<int:g>/<int:b>',
            'fill', view_func=self.clear_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/playlocalgif/<path:file_path>',
            'play_local_gif', view_func=self.play_local_gif,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/playlocalgifdirectory/<path:path>',
            'play_local_gif_directory', view_func=self.play_local_gif_directory,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/playnetgif/<path:gif_file_url>',
            'play_gif_file_url', view_func=self.play_net_gif,
            methods=['GET', 'POST'])
        self.rest.add_url_rule('/push', 'push', view_func=self.push, methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/soundbuzzer/<int:active_cycle_time>/<int:inactive_cycle_time>/<int:total_time>',
            'sound_buzzer', view_func=self.sound_buzzer,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/reboot',
            'reboot', view_func=self.reboot,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/sendtext/<int:x>/<int:y>/<int:r>/<int:g>/<int:b>/<int:identifier>/<int:font>/<int:width>/'
            '<int:movement_speed>/<int:direction>',
            'send_text_at_location_rgb', view_func=self.send_text_at_location_rgb,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setbrightness/<int:brightness>',
            'set_brightness', view_func=self.set_brightness,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setchannel/<int:channel>',
            'set_channel', view_func=self.set_channel,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setclock/<int:clock_id>',
            'set_clock', view_func=self.set_clock,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setface/<int:face_id>',
            'set_face', view_func=self.set_face,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/sethighlight/<int:on>',
            'set_high_light_mode', view_func=self.set_high_light_mode,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setmirror/<int:on>',
            'set_mirror_mode', view_func=self.set_mirror_mode,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setnoise/<int:on>',
            'set_noise_status', view_func=self.set_noise_status,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setscoreboard/<int:blue_score>/<int:red_score>',
            'set_score_board', view_func=self.set_score_board,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setscreen/<int:on>',
            'set_screen', view_func=self.set_screen,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setvisualizer/<int:equalizer_position>',
            'set_visualizer', view_func=self.set_visualizer,
            methods=['GET', 'POST'])
        self.rest.add_url_rule(
            '/setwhitebalance/<int:white_balance_r>/<int:white_balance_g>/<int:white_balance_b>',
            'set_white_balance_rgb', view_func=self.set_white_balance_rgb,
            methods=['GET', 'POST'])

        self.rest.run(rest_configuration.host, rest_configuration.port, rest_configuration.debug)

    def clear_rgb(self, r, g, b):
        self.pixoo.clear_rgb(r, g, b)

        return self.__respond_success()

    def draw_character_at_location_rgb(self, character, x, y, r, g, b):
        self.pixoo.draw_character_at_location_rgb(character, x, y, r, g, b)

        return self.__respond_success()

    def draw_filled_rectangle_from_top_left_to_bottom_right_rgb(self,
                                                                top_left_x=0,
                                                                top_left_y=0,
                                                                bottom_right_x=1,
                                                                bottom_right_y=1,
                                                                r=0, g=0, b=0):
        self.pixoo.draw_filled_rectangle_from_top_left_to_bottom_right_rgb(top_left_x, top_left_y, bottom_right_x,
                                                                           bottom_right_y, r, g, b)

        return self.__respond_success()

    def draw_line_from_start_to_stop_rgb(self, start_x, start_y, stop_x, stop_y,
                                         r=255, g=255, b=255):
        self.pixoo.draw_line_from_start_to_stop_rgb(start_x, start_y, stop_x, stop_y, r, g, b)

        return self.__respond_success()

    def draw_pixel_at_index_rgb(self, index, r, g, b):
        self.pixoo.draw_pixel_at_index_rgb(index, r, g, b)

        return self.__respond_success()

    def draw_pixel_at_location_rgb(self, x, y, r, g, b):
        self.pixoo.draw_pixel_at_location_rgb(x, y, r, g, b)

        return self.__respond_success()

    def draw_text_at_location_rgb(self, text, x, y, r, g, b):
        self.pixoo.draw_text_at_location_rgb(text, x, y, r, g, b)

        return self.__respond_success()

    def get_all_device_configurations(self):
        return self.pixoo.get_all_device_configurations()

    def get_device_time(self):
        return self.pixoo.get_device_time()

    def play_local_gif(self, file_path):
        self.pixoo.play_local_gif(file_path)

        return self.__respond_success()

    def play_local_gif_directory(self, path):
        self.pixoo.play_local_gif_directory(path)

        return self.__respond_success()

    def play_net_gif(self, gif_file_url):
        self.pixoo.play_net_gif(gif_file_url)

        return self.__respond_success()

    def push(self):
        self.pixoo.push()

        return self.__respond_success()

    def reboot(self):
        self.pixoo.reboot()

        return self.__respond_success()

    def send_text_at_location_rgb(self, text, x=0, y=0, r=255, g=255, b=255, identifier=1, font=2, width=64,
                                  movement_speed=0,
                                  direction=TextScrollDirection.LEFT):
        self.pixoo.send_text_at_location_rgb(text, x, y, r, g, b, identifier, font, width, movement_speed, direction)

        return self.__respond_success()

    def set_brightness(self, brightness):
        self.pixoo.set_brightness(brightness)

        return self.__respond_success()

    def set_channel(self, channel):
        self.pixoo.set_channel(channel)

        return self.__respond_success()

    def set_clock(self, clock_id):
        self.pixoo.set_clock(clock_id)

        return self.__respond_success()

    def set_face(self, face_id):
        self.pixoo.set_face(face_id)

        return self.__respond_success()

    def set_high_light_mode(self, on=1):
        self.pixoo.set_high_light_mode(on)

        return self.__respond_success()

    def set_mirror_mode(self, on=0):
        self.pixoo.set_mirror_mode(on)

        return self.__respond_success()

    def set_noise_status(self, on=1):
        self.pixoo.set_noise_status(on)

        return self.__respond_success()

    def set_score_board(self, blue_score, red_score):
        self.pixoo.set_score_board(blue_score, red_score)

        return self.__respond_success()

    def set_screen(self, on=1):
        self.pixoo.set_screen(on)

        return self.__respond_success()

    def set_visualizer(self, equalizer_position):
        self.pixoo.set_visualizer(equalizer_position)

        return self.__respond_success()

    def set_white_balance_rgb(self, white_balance_r, white_balance_g, white_balance_b):
        self.pixoo.set_white_balance_rgb(white_balance_r, white_balance_g, white_balance_b)

        return self.__respond_success()

    def sound_buzzer(self, active_cycle_time=500, inactive_cycle_time=500, total_time=3000):
        self.pixoo.sound_buzzer(active_cycle_time, inactive_cycle_time, total_time)

        return self.__respond_success()

    @staticmethod
    def __respond_success():
        return jsonify({'success': True})
