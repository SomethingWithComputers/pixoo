def clamp(value, minimum=0, maximum=255):
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum

    return value


def clamp_color(rgb):
    return clamp(rgb[0]), clamp(rgb[1]), clamp(rgb[2])


def lerp(start, end, interpolant):
    return start + interpolant * (end - start)


def lerp_location(xy1, xy2, interpolant):
    return lerp(xy1[0], xy2[0], interpolant), lerp(xy1[1], xy2[1], interpolant)


def minimum_amount_of_steps(xy1, xy2):
    return max(abs(xy1[0] - xy2[0]), abs(xy1[1] - xy2[1]))


def rgb_to_hex_color(rgb):
    return f'#{rgb[0]:0>2X}{rgb[1]:0>2X}{rgb[2]:0>2X}'


def round_location(xy):
    return round(xy[0]), round(xy[1])
