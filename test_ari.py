#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import ari
import logging
import time

logging.basicConfig(level=logging.DEBUG)
load_dotenv(override=True)
ast_url = os.getenv("ARI_SERVER", 'http://localhost:8088')
ast_username = os.getenv("ARI_USERNAME", 'asterisk')
ast_password = os.getenv("ARI_PASSWORD", 'asterisk')
ast_app = os.getenv("ARI_APP", 'test-ari')
client = ari.connect(ast_url, ast_username, ast_password)

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
client.run(apps=ast_app)
