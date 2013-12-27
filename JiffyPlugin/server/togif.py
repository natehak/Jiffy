#! /usr/bin/python -O
# Youtube to GIF
# A utility for turning YouTube links into GIFs
# Usage: ./togif.py

# Copyright Nathan Hakkakzadeh and John O'Reilly 2013

'''
 This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


    Please also refer to the stipulations defined in the README file.
'''

from subprocess import check_call
import subprocess
import string
import random
import glob
from base64 import b64encode
import requests
import html.parser
import sys
import configparser

# Etc.
DEVNULL = open("/dev/null", "w")
PATH = "/home/jiffy/jiffy-reddit/"

# Set up config so we can get basic data
config = configparser.ConfigParser()
config.read(PATH + "jiffy.cfg")

# Constants
# Imgur related
API_KEY = config.get("Imgur", "client_id")
URL = "https://api.imgur.com/3/upload.json"
HEADERS = {"Authorization": "Client-ID " + API_KEY}

# Path to plugin
PATH = config.get("Path", "path")

# YouTube related
YT_USERNAME = config.get("YouTube", "username")
YT_PASSWORD = config.get("YouTube", "password")


# Random string generator
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


# Log to a log file
def log_image_created(imgur_link):
    with open("jiffyplugin.log", "w") as f:
        f.write("GIF Created: " + imgur_link + "\n")
        f.flush()


# Upload to imgur function
def imgur_upload(path):
    request = requests.post(
        URL,
        headers=HEADERS,
        data={
            'key': API_KEY,
            'image': b64encode(open(path, 'rb').read()),
            'type': 'base64',
            'name': path,
            'title': path + " by Jiffy"
        })

    return request.json()["data"]["link"]


# Returns imgur link
def youtubetogif(youtubelink, token, start, stop):
    place = PATH + "tmp/" + token
    try:

        # Parse the time
        starts = [int(x) for x in start.split(":")[::-1]]
        stops = [int(x) for x in stop.split(":")[::-1]]

        diff = []

        for i in range(0, len(starts)):
            diff.append(stops[i] - starts[i])

            if diff[i] < 0:
                stops[i+1] -= 1
                diff[i] += 60

            if diff[0] > 15:
                raise Exception("Length too long.")

            for i in range(1, len(diff)):
                if diff[i] > 0:
                    raise Excpetion("Length too long.")

        reverse_diff = diff[::-1]

        tosend = ""
        for d in reverse_diff:
            tosend += str(d) + ":"

        tosend = tosend[0:len(tosend)-1]

        # Download the YouTube link and save it
        check_call([
            "youtube-dl", "-o", place + "-vid", "-f", "5", "--max-filesize",
            "40m", "-u", YT_USERNAME, "-p", YT_PASSWORD, youtubelink],
            stdout=DEVNULL, stderr=subprocess.STDOUT)

        # Convert to frames
        check_call([
            "ffmpeg", "-ss", start, "-i", place + "-vid", "-t", tosend, "-vf",
            "scale=240:trunc(ow/a/2)*2", "-r", "10",
            place + "-frames%05d.gif"], stdout=DEVNULL,
            stderr=subprocess.STDOUT)

        # Stitch it together as a gif
        files = glob.glob(place + "-frames*.gif")

        arguments = ["gifsicle", "--loop", "--optimize"]
        arguments += files

        with open(place + ".gif", 'w') as image_file:
            check_call(arguments, stdout=image_file)

        # Upload to imgur
        link = imgur_upload(place + ".gif")

    except Exception as e:
        link = "Error GIF Failed"
        if "Length too long." in e.args:
            link = "\n\nYour requested GIF was over 15 seconds."
    finally:
        # Delete unnecessary files
        files = glob.glob(place + "*")
        arguments = ["rm"]
        arguments += files
        check_call(arguments)

        return link


def main(argv):
    if len(argv) < 3:
        print("Please give me a YouTube link :'(")
    else:
        link = youtubetogif(argv[0], id_generator(), argv[1], argv[2])
        print(link)

if __name__ == "__main__":
    main(sys.argv[1:])
