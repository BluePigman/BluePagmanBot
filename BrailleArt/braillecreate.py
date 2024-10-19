from .brailledata import braille_descr_dic
from PIL import Image


treshold = 0
transparency = True


def treshold_dithering(picture, color_threshold=128, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    global treshold, transparency
    treshold = color_threshold
    transparency = fill_transparency
    picture = _resize_pic(picture, width, height)
    result_arr = []

    for y in range(0, picture.height, 4):
        line = ""
        for x in range(0, picture.width, 2):
            line += braille_descr_dic[_get_braille_code(picture, x, y)]
        result_arr.append(line)

    if dot_for_blank:
        return line_delimiter.join(result_arr).replace('⠀', '⠄')
    else:
        return line_delimiter.join(result_arr)


def ordered_dithering(picture, color_threshold=128, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    picture = _resize_pic(picture, width, height)

    change_factor = color_threshold/128
    matrix = [[64*change_factor, 128*change_factor], [192*change_factor, 0]]
    for y in range(0, picture.height, 1):
        for x in range(0, picture.width, 1):
            pixel = picture.getpixel((x, y))
            if sum((pixel[0], pixel[1], pixel[2])) / 3 > matrix[(y % len(matrix))][(x % len(matrix))]:
                picture.putpixel((x, y), (255, 255, 255, pixel[3]))
            else:
                picture.putpixel((x, y), (0, 0, 0, pixel[3]))

    return treshold_dithering(picture, 128, line_delimiter, dot_for_blank, fill_transparency, 0, 0)


def floyd_steinberg_dithering(picture, color_threshold=1, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    picture = _resize_pic(picture, width, height)

    for y in range(0, picture.height, 1):
        for x in range(0, picture.width, 1):
            quant_error = list(picture.getpixel((x, y)))
            oldpixel = picture.getpixel((x, y))
            percent = color_threshold/255
            red_poly = ((1-percent) ** 2)
            green_poly = 2*(1-percent)*percent
            blue_poly = (percent ** 2)

            if red_poly*oldpixel[0] + green_poly*oldpixel[1] + blue_poly*oldpixel[2] > 128:
                for i in range(0, len(quant_error)-1, 1):
                    quant_error[i] -= 255
                picture.putpixel((x, y), (255, 255, 255, oldpixel[3]))
            else:
                picture.putpixel((x, y), (0, 0, 0, oldpixel[3]))

            neighbours = [(1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)]
            for a, b, q in neighbours:
                if x+a < picture.width and x+a > 0 and y+b < picture.height:
                    new_colors = [''] * 3
                    for i in range(0, len(quant_error)-1, 1):
                        new_colors[i] = int(picture.getpixel(
                            (x+a, y+b))[i] + (quant_error[i] * q / 16))
                    picture.putpixel(
                        (x+a, y+b), (new_colors[0], new_colors[1], new_colors[2], picture.getpixel((x+a, y+b))[3]))

    return treshold_dithering(picture, 128, line_delimiter, dot_for_blank, fill_transparency, 0, 0)


def _resize_pic(picture, width, height):
    width = picture.width if width <= 0 else width
    height = picture.height if height <= 0 else height
    picture = picture.resize((width, height), Image.LANCZOS)
    return picture


def _get_braille_code(picture, x, y):
    braille_code = ""
    braille_parts_arr = [  # (x, y, dot number in braille character)
        (0, 0, "1"),
        (0, 1, "2"),
        (0, 2, "3"),
        (0, 3, "7"),
        (1, 0, "4"),
        (1, 1, "5"),
        (1, 2, "6"),
        (1, 3, "8")
    ]
    for xn, yn, p in braille_parts_arr:
        if y + yn < picture.height and x + xn < picture.width:
            if _evaluate_pixel(*picture.getpixel((x + xn, y + yn))):
                braille_code += p

    return ''.join(sorted(braille_code))


def _evaluate_pixel(red, green, blue, alpha):
    if transparency and alpha == 0:
        return False
    if red > treshold or green > treshold or blue > treshold:
        return False
    else:
        return True
