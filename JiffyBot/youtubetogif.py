#! /usr/bin/python -O
# Youtube to GIF
# A reddit bot for turning YouTube links into GIFs
# Usage: ./youtubetogif.py

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
import praw
import time
import threading
import re
import html.parser
import sys
import configparser

# Set up config so we can get basic data
config = configparser.ConfigParser()
config.read("jiffy.cfg")

# Constants
# Imgur related
API_KEY = config.get("Imgur", "client_id")
URL = "https://api.imgur.com/3/upload.json"
HEADERS = {"Authorization": "Client-ID " + API_KEY}

# Reddit related
USERNAME = config.get("Reddit", "username")
PASSWORD = config.get("Reddit", "password")
COMMENT_TEMPLATE = ("Here's your GIF!\n\n{0}\n\n_____\n^(Hey I'm JiffyBot, I "
                    "make GIFs out of YouTube links. Find out more) [^here.]("
                    "http://www.reddit.com/r/JiffyBot/comments/1fvyi5/rjiffyb"
                    "ot_information_directory/)")
MULTI_TEMPLATE = ("Here are your GIFs!\n\n{0}\n\n_____\n^(Hey I'm JiffyBot, I"
                  "make GIFs out of YouTube links. Find out more) [^here.](ht"
                  "tp://www.reddit.com/r/JiffyBot/comments/1fvyi5/rjiffybot_i"
                  "nformation_directory/)")

# YouTube related
YT_USERNAME = config.get("YouTube", "username")
YT_PASSWORD = config.get("YouTube", "password")

# Etc.
DEVNULL = open("/dev/null", "w")
# Objects
# Reddit related
r = praw.Reddit(user_agent="JiffyBot by /u/drkabob/. Converts YouTube links to\
    GIFs.")
r.login(USERNAME, PASSWORD)
html_parser = html.parser.HTMLParser()
commented = []
blacklist = []
last_mention = time.time()


# Random string generator
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


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


# Convenience function for finding parent of comment
def ParentObj(reddit, obj):
    assert type(obj) == praw.objects.Comment
    if obj.is_root:
        return obj.submission
    return reddit.get_info(thing_id=obj.parent_id)


# Function is blocking, so it should be run in a separate thread
# Works with any video link youtube-dl supports
# Returns imgur link
def youtubetogif(youtubelink, token, start, stop):

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
            "youtube-dl", "-o", token + "-vid", "-f", "5", "--max-filesize",
            "40m", "-u", YT_USERNAME, "-p", YT_PASSWORD, youtubelink],
            stdout=DEVNULL, stderr=subprocess.STDOUT)

        # Convert to frames
        check_call([
            "ffmpeg", "-ss", start, "-i", token + "-vid", "-t", tosend, "-vf",
            "scale=240:trunc(ow/a/2)*2", "-r", "10",
            token + "-frames%05d.gif"], stdout=DEVNULL,
            stderr=subprocess.STDOUT)

        # Stitch it together as a gif
        files = glob.glob(token + "-frames*.gif")

        arguments = ["gifsicle", "--loop", "--optimize"]
        arguments += files

        with open(token + ".gif", 'w') as image_file:
            check_call(arguments, stdout=image_file)

        # Upload to imgur
        link = imgur_upload(token + ".gif")

    except Exception as e:
        link = ("[Error! GIF failed :(](http://www.reddit.com/r/JiffyBot/comm"
                "ents/1gdlog/why_isnt_my_gif_workingtips_on_making_a_gif/)")
        print(e)
        if "Length too long." in e.args:
            link += "\n\nYour requested GIF was over 15 seconds."

    finally:
        # Delete unnecessary files
        files = glob.glob(token + "*")

        arguments = ["rm"]
        arguments += files
        check_call(arguments)

        return link


def reply_to_comment(comment, youtubelink, start, stop):

    link = youtubetogif(youtubelink, id_generator(), start, stop)
    comment.reply(COMMENT_TEMPLATE.format(link, youtubelink))
    commented.append(comment)


def multi_reply_to_comment(comment, youtubelink, times):
    torespond = []
    for time in times:
        times = time.split("-")
        torespond.append(
            youtubetogif(youtubelink, id_generator(), times[0], times[1]))
    tosend = "\n".join(torespond)
    comment.reply(MULTI_TEMPLATE.format(tosend, youtubelink))
    commented.append(comment)


def parse_comment_body(comment, yt_link):
    time_loc = re.findall(
        "[0-9]?[0-9]:[0-9][0-9]-[0-9]?[0-9]:[0-9][0-9]", comment.body)
    if time_loc != []:
        if len(time_loc) > 1:
            threading.Thread(
                target=multi_reply_to_comment, args=(
                    comment, html_parser.unescape(yt_link), time_loc)).start()
        else:
            times = time_loc[0].split("-")
            threading.Thread(
                target=reply_to_comment, args=(
                    comment, html_parser.unescape(yt_link), times[0],
                    times[1])).start()


# Searches a comment for a YouTube link
def search_comment(comment):
    if type(comment) == praw.objects.Submission:
        search_field = comment.url
    else:
        search_field = comment.body
    yt_loc = re.findall("https?://www.youtube.com/.*", search_field)
    yt_loc += re.findall("https?://youtu.be/.*", search_field)
    yt_loc += re.findall("https?://m.youtube.com/.*", search_field)

    if yt_loc != []:
        return yt_loc[0]
    else:
        return False


def parse_comment(comment):
    if (comment not in commented and
            str(comment.subreddit.display_name) not in blacklist):

        yt_link = search_comment(comment)
        #yt_link_parent = search_comment(ParentObj(r, comment))
        # YouTube link is in comment
        if yt_link:
            parse_comment_body(comment, yt_link)

        # YouTube link is in parent comment
        #elif yt_link_parent != False:
        #	parse_comment_body(comment, yt_link)

        # YouTube link is in submission
        elif ("youtube" in comment.submission.url or
                "youtu.be" in comment.submission.url):
            parse_comment_body(comment, comment.submission.url)


# Main loop for comment searching and parsing
def main_loop():
    global last_mention
    # Main loop start here...
    while True:
        # Read the blacklist and place it into an array
        with open("blacklist.txt", 'r') as f:
            del blacklist[:]
            for entry in f.readlines():
                blacklist.append(entry.strip())

        # Read read list for mentioned
#        with open("readlist.txt", 'r') as f:
#            lasttime = 0
#            for entry in f.readlines():
#                lasttime = float(entry)

        # Start the comment loop
        try:
            # Grab as many comments as we can and loop through them
            for comment in r.get_comments("all", limit=None):
                # Check if the comment meets the basic criteria
                if "Jiffy!" in comment.body:
                    parse_comment(comment)

            # Check mentions
            for comment in r.get_mentions():
                if (comment.created_utc - last_mention) > 0:
                    with open("readlist.txt", "w") as f:
                        f.write(str(comment.created_utc))
                    last_mention = comment.created_utc
                    parse_comment(comment)

            # Finally wait 30 seconds
            time.sleep(30)
        except Exception as e:
            print(e)

# Threads!
main_thread = threading.Thread(target=main_loop)

# Start threads!
main_thread.start()
