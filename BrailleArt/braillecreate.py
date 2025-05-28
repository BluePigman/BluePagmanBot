from .brailledata import braille_descr_dic
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np


def treshold_dithering(picture, color_threshold=128, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    picture = _resize_pic(picture, width, height)
    result_arr = []

    for y in range(0, picture.height, 4):
        line = ""
        for x in range(0, picture.width, 2):
            line += braille_descr_dic[_get_braille_code(picture, x, y, color_threshold, fill_transparency)]
        result_arr.append(line)

    if dot_for_blank:
        # For black background, use single dot instead of centered dot
        return line_delimiter.join(result_arr).replace('⠀', '⠁')
    else:
        return line_delimiter.join(result_arr)


def ordered_dithering(picture, color_threshold=128, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    picture = _resize_pic(picture, width, height)
    
    # Apply preprocessing for better results
    picture = apply_gamma_correction(picture, 0.7)
    picture = enhance_contrast(picture, 1.5)
    picture = simple_edge_enhance(picture)

    change_factor = color_threshold/128
    matrix = [[64*change_factor, 128*change_factor], [192*change_factor, 0]]
    for y in range(0, picture.height, 1):
        for x in range(0, picture.width, 1):
            pixel = picture.getpixel((x, y))
            # Use perceptually accurate grayscale conversion
            gray_value = _rgb_to_grayscale(pixel[0], pixel[1], pixel[2])
            if gray_value > matrix[(y % len(matrix))][(x % len(matrix))]:
                picture.putpixel((x, y), (255, 255, 255, pixel[3]))
            else:
                picture.putpixel((x, y), (0, 0, 0, pixel[3]))

    return treshold_dithering(picture, 128, line_delimiter, dot_for_blank, fill_transparency, 0, 0)


def floyd_steinberg_dithering(picture, color_threshold=128, line_delimiter=' ', dot_for_blank=True, fill_transparency=True, width=0, height=0):
    picture = _resize_pic(picture, width, height)
    
    # Apply preprocessing for better results
    picture = apply_gamma_correction(picture, 0.7)
    picture = enhance_contrast(picture, 1.5)
    picture = simple_edge_enhance(picture)

    for y in range(0, picture.height, 1):
        for x in range(0, picture.width, 1):
            quant_error = list(picture.getpixel((x, y)))
            oldpixel = picture.getpixel((x, y))
            # Use perceptually accurate grayscale
            gray_value = _rgb_to_grayscale(oldpixel[0], oldpixel[1], oldpixel[2])
            
            if gray_value > 128:
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

    return treshold_dithering(picture, color_threshold, line_delimiter, dot_for_blank, fill_transparency, 0, 0)


def _resize_pic(picture, width, height):
    width = picture.width if width <= 0 else width
    height = picture.height if height <= 0 else height
    picture = picture.resize((width, height), Image.LANCZOS)
    return picture


def _get_braille_code(picture, x, y, threshold, transparency):
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
            pixel = picture.getpixel((x + xn, y + yn))
            if _evaluate_pixel(pixel[0], pixel[1], pixel[2], pixel[3], threshold, transparency):
                braille_code += p

    return ''.join(sorted(braille_code))


def _evaluate_pixel(red, green, blue, alpha, threshold, transparency):
    if transparency and alpha == 0:
        return False
    
    # For black background, we want to show bright pixels as dots
    brightness = _rgb_to_grayscale(red, green, blue)
    
    # Invert the logic for black backgrounds
    return brightness > threshold


def _rgb_to_grayscale(r, g, b):
    """Convert RGB to grayscale using perceptually accurate weights"""
    return int(0.2126 * r + 0.7152 * g + 0.0722 * b)


def apply_gamma_correction(picture, gamma=0.7):
    """Apply gamma correction to brighten mid-tones for better visibility on black backgrounds"""
    # Convert to numpy array for efficient processing
    img_array = np.array(picture)
    
    # Apply gamma correction
    corrected = np.power(img_array / 255.0, gamma) * 255
    
    # Convert back to PIL Image
    return Image.fromarray(corrected.astype(np.uint8))


def enhance_contrast(picture, factor=1.5):
    """Enhance contrast for better definition at low resolutions"""
    enhancer = ImageEnhance.Contrast(picture)
    return enhancer.enhance(factor)


def simple_edge_enhance(picture):
    """Apply gentle edge enhancement suitable for small images"""
    return picture.filter(ImageFilter.EDGE_ENHANCE)