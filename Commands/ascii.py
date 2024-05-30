import os
import sys
import time
import re
from PIL import Image, UnidentifiedImageError, ImageSequence
import requests
from io import BytesIO
import argparse
from pymongo import MongoClient

# Add the parent directory of the current script to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BrailleArt import braillecreate, brailletransform

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)
    
    def exit(self, status=0, message=None):
        if message:
            raise argparse.ArgumentError(None, message)

def parse_custom_args(args):
    parser = CustomArgumentParser(description="Process image to ASCII art.", add_help=False)
    parser.add_argument('-w', type=int, default=60, help="Sets the width of the ASCII in pixels.")
    parser.add_argument('-h', type=int, default=60, help="Sets the height of the ASCII in pixels.")
    parser.add_argument('-r', type=int, choices=[90, 180, 270], help="Rotates the ASCII given degrees.")
    parser.add_argument('-tr', type=int, default=128, help="Static threshold dithering (0-255).")
    parser.add_argument('-d', action='store_true', help="Use Floyd-Steinberg dithering.")
    parser.add_argument('-b', action='store_false', help="Remove transparent background.")
    parser.add_argument('-e', action='store_false', help="Keep empty characters.")
    parser.add_argument('-i', action='store_true', help="Invert the end result.")
    parser.add_argument('-g', action='store_true', help="Use multiple frames of the first gif provided.")
    parser.add_argument('-t', type=str, help="Text to print on the ASCII.")
    
    # Custom help argument to avoid conflict with -h for height
    parser.add_argument('--help', action='help', help="Show this help message and exit.")

    try:
        parsed_args = parser.parse_args(args)
        return vars(parsed_args)
    except argparse.ArgumentError as e:
        raise argparse.ArgumentError(None, str(e))

def reply_with_ascii(bot, message):
    if message.user not in bot.state or time.time() - bot.state[message.user] > bot.cooldown:
        bot.state[message.user] = time.time()
        
        # Validate if the first argument is a URL or an emote name
        if not message.text_args:
            m = f"@{message.user}, please provide a URL of the image or a global emote name."
            bot.send_privmsg(message.channel, m)
            return

        input_arg = message.text_args[0]
        if re.match(r'((ftp|http|https)://.+)|(\./frames/.+)', input_arg):
            image_url = input_arg
        else:
            # Check if the input is an emote name and retrieve the URL from the database
            emote = bot.db['Emotes'].find_one({"name": input_arg})
            if emote:
                image_url = emote['url']
            else:
                m = f"@{message.user}, could not find the emote '{input_arg}' in the database."
                bot.send_privmsg(message.channel, m)
                return
        
        try:
            args = parse_custom_args(message.text_args[1:])
        except Exception as e:
            bot.send_privmsg(message.channel, "Error parsing arguments: " + str(e) + f". Run {bot.command_prefix}ascii_help for more info.")
            return
        
        resp = requests.get(image_url)
        if resp.status_code == 200:
            img_bytes = resp.content
        else:
            bot.send_privmsg(message.channel, "The image could not be loaded. :Z")
            return
        
        try:
            image = Image.open(BytesIO(img_bytes))

            frames = []
            if getattr(image, "is_animated", False):
                total_frames = image.n_frames
                max_frames = 20

                if total_frames > max_frames:
                    # Calculate the interval to sample frames
                    interval = total_frames // max_frames
                else:
                    interval = 1

                # Extract frames based on the calculated interval
                for i, frame in enumerate(ImageSequence.Iterator(image)):
                    if i % interval == 0:
                        frame = frame.convert('RGBA')
                        frames.append(frame)
                        if len(frames) >= max_frames:
                            break
            else:
                frames.append(image)
                
            for frame in frames:
                frame = frame.convert("RGBA")
                image_str = ""
                if args['d']:
                    image_str = braillecreate.floyd_steinberg_dithering(frame, color_treshold=args['tr'], fill_transparency=args['b'], dot_for_blank= args['e'], width=args['w'], height=args['h'])
                else:
                    image_str = braillecreate.treshold_dithering(frame, color_treshold=args['tr'], dot_for_blank= args['e'], fill_transparency=args['b'], width=args['w'], height=args['h'])
                
                image_str = brailletransform.invert(image_str, args['e'])
                
                if len(image_str) > 499:
                    m = "The image is too long to display in a message. :Z Try using smaller values for -w and/or -h. \
                    If you tried negative values, please use positive ones. Staring "
                    bot.send_privmsg(message.channel, m)
                    break

                if args['i']:
                    image_str = brailletransform.invert(image_str, args['e'])
                if args['r'] == 90:
                    image_str = brailletransform.turn_90(image_str, dot_for_blank= args['e'])
                elif args['r'] == 180:
                    image_str = brailletransform.turn_180(image_str, dot_for_blank= args['e'])
                elif args['r'] == 270:
                    image_str = brailletransform.turn_270(image_str, dot_for_blank= args['e'])

                if args['t']:
                    image_str += f"\n{args['t']}"

                bot.send_privmsg(message.channel, image_str)
                time.sleep(0.1)

        except UnidentifiedImageError:
            bot.send_privmsg(message.channel, "The link was not a valid image. :Z")
