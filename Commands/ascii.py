import time
import re
from PIL import Image, UnidentifiedImageError, ImageSequence
import requests
from io import BytesIO
import argparse

from BrailleArt import braillecreate, brailletransform


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise argparse.ArgumentError(None, message)

    def exit(self, status=0, message=None):
        if message:
            raise argparse.ArgumentError(None, message)


def parse_custom_args(args):
    parser = CustomArgumentParser(
        description="Process image to ASCII art.", add_help=False)
    parser.add_argument('-w', type=int, default=60,
                        help="Sets the width of the ASCII in pixels.")
    parser.add_argument('-h', type=int, default=60,
                        help="Sets the height of the ASCII in pixels.")
    parser.add_argument(
        '-r', type=int, choices=[90, 180, 270], help="Rotates the ASCII given degrees.")
    parser.add_argument('-tr', type=int, default=128,
                        help="Static threshold dithering (0-255).")
    parser.add_argument('-d', action='store_true',
                        help="Use Floyd-Steinberg dithering.")
    parser.add_argument('-b', action='store_false',
                        help="Remove transparent background.")
    parser.add_argument('-e', action='store_false',
                        help="Keep empty characters.")
    parser.add_argument('-i', action='store_true',
                        help="Invert the end result.")
    parser.add_argument('-g', action='store_true',
                        help="Use multiple frames of the first gif provided.")
    parser.add_argument('-t', type=str, help="Text to print on the ASCII.")

    # Custom help argument to avoid conflict with -h for height
    parser.add_argument('--help', action='help',
                        help="Show this help message and exit.")

    try:
        parsed_args = parser.parse_args(args)
        return vars(parsed_args)
    except argparse.ArgumentError as e:
        raise


def reply_with_ascii(self, message):
    if message['source']['nick'] not in self.state or time.time() - self.state[message['source']['nick']] > self.cooldown:
        self.state[message['source']['nick']] = time.time()

        # Validate if the first argument is a URL or an emote name
        if not message['command']['botCommandParams']:
            m = f"@{message['tags']['display-name']}, please provide a URL of the image or a global emote name."
            self.send_privmsg(message['command']['channel'], m)
            return
        if "\U000e0000" in message['command']['botCommandParams']:
            message['command']['botCommandParams'].remove("\U000e0000")
        input_arg = message['command']['botCommandParams'].split()
        channel_id = message["tags"]["room-id"]
        user_display_name = message['tags']['display-name']
        
        # Check if the input is a URL
        if re.match(r'((ftp|http|https)://.+)|(\./frames/.+)', input_arg[0]):
            # Set image_url directly if input is a URL
            image_url = input_arg[0]
        
        else:
            # Check if the input is an emote name in the Emotes collection
            emote = self.db['Emotes'].find_one({"name": input_arg[0]})
            if emote:
                emote_id = emote['emote_id']
                is_global = emote.get("is_global", False)
                
                # Verify that the emote is either global or associated with the specified channel
                if is_global or self.db['ChannelEmotes'].find_one({"channel_id": channel_id, "emote_id": emote_id}):
                    # Set image_url if emote is valid as global or channel-specific
                    image_url = emote['url']
                else:
                    # Emote is not available in the specified channel
                    m = f"@{user_display_name}, the emote '{input_arg[0]}' is not available as a global/channel emote."
                    self.send_privmsg(message['command']['channel'], m)
                    return
            else:
                # Emote not found in the Emotes collection
                m = f"@{user_display_name}, could not find the emote '{input_arg[0]}' in the database. Try using a URL instead."
                self.send_privmsg(message['command']['channel'], m)
                return
        try:
            args = parse_custom_args(input_arg[1:])
        except Exception as e:
            self.send_privmsg(message['command']['channel'], "Error parsing arguments: " + str(
                e) + f". Run {self.prefix}help_ascii for more info.")
            return

        try:
            resp = requests.get(image_url)
            img_bytes = resp.content
        except Exception:
            self.send_privmsg(message['command']['channel'],
                             f"Error, URL was invalid. FailFish")
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

                # Ensure the last frame is included
                image.seek(total_frames - 1)
                last_frame = image.convert('RGBA')
                if last_frame not in frames:
                    frames.append(last_frame)
            else:
                frames.append(image)

            for frame in frames:
                frame = frame.convert("RGBA")
                image_str = ""
                if args['d']:
                    image_str = braillecreate.floyd_steinberg_dithering(
                        frame, color_threshold=args['tr'], fill_transparency=args['b'], dot_for_blank=args['e'], width=args['w'], height=args['h'])
                else:
                    image_str = braillecreate.treshold_dithering(
                        frame, color_threshold=args['tr'], dot_for_blank=args['e'], fill_transparency=args['b'], width=args['w'], height=args['h'])

                image_str = brailletransform.invert(image_str, args['e'])

                if len(image_str) > 499:
                    m = "The image is too long to display in a message. :Z Try using smaller values for -w and/or -h. \
                    If you tried negative values, please use positive ones. Staring "
                    self.send_privmsg(message['command']['channel'], m)
                    break

                if args['i']:
                    image_str = brailletransform.invert(image_str, args['e'])
                if args['r'] == 90:
                    image_str = brailletransform.turn_90(
                        image_str, dot_for_blank=args['e'])
                elif args['r'] == 180:
                    image_str = brailletransform.turn_180(
                        image_str, dot_for_blank=args['e'])
                elif args['r'] == 270:
                    image_str = brailletransform.turn_270(
                        image_str, dot_for_blank=args['e'])

                if args['t']:
                    image_str += f"\n{args['t']}"

                self.send_privmsg(message['command']['channel'], image_str)
                time.sleep(0.1)

        except UnidentifiedImageError:
            self.send_privmsg(message['command']['channel'],
                             "The link was not a valid image. :Z")


def first_frame(channel, emote_url):
    # get first frame of ascii
    try:
        resp = requests.get(emote_url)
        img_bytes = resp.content
    except Exception as e:
        print(e)
        return f"An error occurred while retrieving the image: {str(e)}"

    try:
        image = Image.open(BytesIO(img_bytes))
        frames = []
        if getattr(image, "is_animated", False):
            total_frames = image.n_frames
            max_frames = 20

            interval = total_frames // max_frames if total_frames > max_frames else 1

            # Extract frames based on the calculated interval
            for i, frame in enumerate(ImageSequence.Iterator(image)):
                if i % interval == 0:
                    frame = frame.convert('RGBA')
                    frames.append(frame)
                    if len(frames) >= max_frames:
                        break
        else:
            frames.append(image)

        frame = frames[0]
        frame = frame.convert("RGBA")
        image_str = ""
        image_str = braillecreate.treshold_dithering(
            frame, width=60, height=60)
        return image_str
    except UnidentifiedImageError:
        return "The link was not a valid image. :Z"
