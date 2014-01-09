#!/usr/bin/env python

# This is a quickly hacked script to turn the ccc.media.de's podcast.xml, 
# released for each Chaos Communication Congress, into XBMC *.nfo files.
#
# To find these files go to http://media.ccc.de/browse/congress/<INSERT YEAR HERE>/podcast.xml
#
# (c) 2014 by Florian Franzen

# ToDo: Add curl to download xml.

import argparse

import xml.etree.ElementTree as ET
import re
import codecs
import os
from collections import namedtuple

Talk = namedtuple("Talk", "title subtitle description speakers category prefix")


parser = argparse.ArgumentParser(description='Creates NFO files for each entry in a podcast.xml file.')
parser.add_argument('YEAR', type=int, help='The conference the podcast.xml is from e.g. 30 if you run this for the 30c3.')
parser.add_argument('XML_FILE', help='Path to the xml file.')
config = parser.parse_args()


def createNFO(episode, id_num, talk, season, num_digit=2):
    xml_file = r"""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <episodedetails>
    <showtitle>Chaos Communication Congress</showtitle>
    <season>%d</season>
    <episode>%d</episode>
    <title>%s</title>
    <outline>%s</outline>
    <year>%s</year>
    <id>%s</id>
    <plot>
        %s
    </plot>
    <genre>Talk</genre>
    <tag>%s</tag>
    """ % (season, episode, talk.title, talk.subtitle, 1983 + season, id_num, talk.description, talk.category)

    for speaker in talk.speakers:
        xml_file += r"""<actor>
        <name>%s</name>
        <role></role>
    </actor>
    """ % speaker.strip()

    xml_file += r"</episodedetails>"

    file_pointer = codecs.open(talk.prefix + "_h264-hq.s%02de%0*d.nfo" % (season, num_digit, episode), "w", "utf-8-sig")
    file_pointer.write(xml_file)
    file_pointer.close()

# Parse XML file first
tree = ET.parse(config.XML_FILE)
root = tree.getroot()

# Make sure directory exist
directory = 'S%02d/' % config.YEAR
if not os.path.exists(directory):
    os.makedirs(directory)
os.chdir(directory)

# Parse all talks
all_talks = dict()

for item in root[0].findall('item'):
    title = item.find('title').text[6:]

    subtitle = item.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle')
    if subtitle is not None:
        subtitle = subtitle.text

    category = item.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}keywords').text

    speakers = item.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}author').text.split(",")

    description = item.find('description').text
    description = re.split('event on media: |about this event: ', description)[0].strip()

    # Extract prefix from link
    link = item.find('link').text
    match = re.search(r'(?<=/)[^/]*(?=(_webm.webm|_h264(-hq|-iprod)?.mp4))', link)
    if match is not None:
        prefix = match.group(0)
    else:
        print("Can not extract prefix from following link: ", link)

    # Extract id from prefix
    match = re.search(r'(?<=\d{2}c3-)\d{4}(?=-)', prefix)
    if match is not None:
        id_num = int(match.group(0))
    else:
        print("Can not extract ID from prefix: ", prefix)

    all_talks[id_num] = Talk(title, subtitle, description, speakers, category, prefix)

# Compute length of zero padding
num_talks = len(all_talks)
num_digit = 0
while num_talks != 0:
    num_digit += 1
    num_talks //= 10

# For each talk...
rename_file = "#! /bin/sh\n"
episode = 1
for id_num in sorted(all_talks):
    talk = all_talks[id_num]

    # ... create NFO files
    createNFO(episode, id_num, talk, config.YEAR, num_digit)

    # ... collect the file names for the renaming script
    rename_file += "mv '%s' '%s'\n" % (talk.prefix + "_h264-hq.mp4", talk.prefix + "_h264-hq.s30e%0*d.mp4" % (num_digit, episode))

    episode += 1

# Save rename script
f = open("rename.sh", "w")
f.write(rename_file)
f.close()
