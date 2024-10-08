#!/usr/bin/env python3

"""Example demonstrating using the returned object from an API call.

This app plays demo-contrats on any channel sent to Stasis(hello). DTMF keys
are used to control the playback.
"""

import sys
sys.path.insert(0, '%s/..' % (sys.path[0]))  # noqa

#
# Copyright (c) 2013, Digium, Inc.
#

import logging
logging.basicConfig(level=logging.DEBUG)

import ari
import sys

client = ari.connect('http://localhost:8088/', 'asterisk', 'secret')


def on_start(channel, event):
    """Callback for StasisStart events.

    On new channels, answer, play demo-congrats, and register a DTMF listener.

    :param channel: Channel DTMF was received from.
    :param event: Event.
    """
    channel.answer()
    playback = channel.play(media='sound:demo-congrats')

    def on_dtmf(channel, event):
        """Callback for DTMF events.

        DTMF events control the playback operation.

        :param channel: Channel DTMF was received on.
        :param event: Event.
        """
        # Since the callback was registered to a specific channel, we can
        #  control the playback object we already have in scope.
        digit = event['digit']
        if digit == '5':
            playback.control(operation='pause')
        elif digit == '8':
            playback.control(operation='unpause')
        elif digit == '4':
            playback.control(operation='reverse')
        elif digit == '6':
            playback.control(operation='forward')
        elif digit == '2':
            playback.control(operation='restart')
        elif digit == '#':
            playback.stop()
            channel.continueInDialplan()
        else:
            print("Unknown DTMF %s" % digit)

    channel.on_event('ChannelDtmfReceived', on_dtmf)


client.on_channel_event('StasisStart', on_start)

# Run the WebSocket
client.run(apps='test-ari')
