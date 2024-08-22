#!/usr/bin/env python3

import sys
sys.path.insert(0, '%s/..' % (sys.path[0]))  # noqa

import os
import ari
import logging
import time

logging.basicConfig(level=logging.DEBUG)
client = ari.connect('http://localhost:8088/', 'asterisk', 'secret')

def on_dtmf(channel, event):
    digit = event['digit']
    if digit == '#':
        channel.play(media='sound:goodbye')
        time.sleep(1)
        channel.hang_up()
    elif digit == '*':
        channel.play(media='sound:asterisk-friend')
    else:
        channel.play(media='sound:digits/%s' % digit)

def on_media_end(channel, event):
    print("Media %s finished on channel %s"%(event['playback']['media_uri'], channel))

def on_start(channel, event):
    channel.on_event('ChannelDtmfReceived', on_dtmf)
    channel.on_event('PlaybackFinished', on_media_end)
    print(channel.get())
    r = channel.answer()
    print(r)
    r = channel.play(media='sound:hello-world')
    print(r)
    print(channel.get())


client.on_channel_event('StasisStart', on_start)
client.run(apps='test-ari')
