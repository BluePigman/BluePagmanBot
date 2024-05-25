import os, sys
import time
import re
from PIL import Image, UnidentifiedImageError
import requests
from io import BytesIO


# Add the parent directory of the current script to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from BrailleArt import braillecreate, brailletransform

def reply_with_ascii(bot, message):
    if (message.user not in bot.state or time.time() - bot.state[message.user] >
            bot.cooldown):
        bot.state[message.user] = time.time()


    
        if not message.text_args or not re.match(r'((ftp|http|https)://.+)|(\./frames/.+)', message.text_args[0]):
            m = f"@{message.user}, please provide a URL of the image (right click emote and copy 4x link in Chatterino)."
            bot.send_privmsg(message.channel, m)
            return
        
        args = parse_custom_args(message.text_args[1:])
        print(args)
        
        resp = requests.get(message.text_args[0])
        if resp.status_code == 200:
            img_bytes = resp.content
        else:
            bot.send_privmsg(message.channel, "The image could not be loaded. :Z")
            return
        try:
            image = Image.open(BytesIO(img_bytes))
            image = image.convert("RGBA")
            image_str = ""
            if args['dithering']:
                image_str = braillecreate.floyd_steinberg_dithering(image, color_treshold=args['threshold'],  fill_transparency=args['background'], dot_for_blank = args['empty'], width=args['width'], height=args['height'])
            else:
                image_str = braillecreate.treshold_dithering(image, color_treshold=args['threshold'], dot_for_blank = args['empty'],  fill_transparency=args['background'], width=args['width'], height=args['height'])

            if args['invert'] == False:
                image_str = brailletransform.invert(image_str, args['empty'])
            if args['rotate'] == 90:
                image_str = brailletransform.turn_90(image_str, args['empty'])
            if args['rotate'] == 180:
                image_str = brailletransform.turn_180(image_str, args['empty'])
            if args['rotate'] == 270:
                image_str = brailletransform.turn_270(image_str, args['empty'])

            bot.send_privmsg(message.channel, image_str)
        except UnidentifiedImageError:
            bot.send_privmsg(message.channel, "The link was not a valid image. :Z")


def parse_custom_args(args):
    options = {
        'width': 60,
        'height': 60,
        'rotate': None,
        'threshold': 128,
        'dithering': False,
        'background': False,
        'empty': True,
        'invert': False,
        'gif': False,
        'text': None
    }
    
    i = 0
    while i < len(args):
        if args[i] == '-w' and i + 1 < len(args):
            options['width'] = int(args[i + 1])
            i += 2
        elif args[i] == '-h' and i + 1 < len(args):
            options['height'] = int(args[i + 1])
            i += 2
        elif args[i] == '-r' and i + 1 < len(args):
            options['rotate'] = int(args[i + 1])
            i += 2
        elif args[i] == '-tr' and i + 1 < len(args):
            options['threshold'] = int(args[i + 1])
            i += 2
        elif args[i] == '-d':
            options['dithering'] = True
            i += 1
        elif args[i] == '-b':
            options['background'] = True
            i += 1
        elif args[i] == '-e':
            options['empty'] = False
            i += 1
        elif args[i] == '-i':
            options['invert'] = True
            i += 1
        elif args[i] == '-g':
            options['gif'] = True
            i += 1
        elif args[i] == '-t' and i + 1 < len(args):
            options['text'] = " ".join(args[i + 1:])
            break
        else:
            i += 1
    
    return options