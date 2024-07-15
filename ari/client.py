import requests
import json
from websockets.sync.client import connect
import logging

from .model import Channel


class Client:
    def __init__(self, url, username, password):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.ws = None
        self.events = {}
        self.objects = {}

    def build_url(self, api):
        return "%s/ari/%s?api_key=%s:%s" % (self.url, api, self.username, self.password);

    def get_object(self, object_type, object_id):
        key = (object_type, object_id)
        if key in self.objects:
            return self.objects[key]
        new_object = object_type(client=self, id=object_id)
        self.objects[key] = new_object
        return new_object

    def del_object(self, object_to_delete):
        if object_to_delete is None or object_to_delete.id is None:
            return
        key = (type(object_to_delete), object_to_delete.id)
        if key in self.objects:
            del(self.objects[key])

    def connect(self):
        r = requests.get(self.build_url("api-docs/resources.json"))
        r.raise_for_status()
        assert len(r.json()["apis"]) > 0

    def on_channel_event(self, event_type, callback):
        self.events[event_type] = callback

    def run(self, apps="no-name"):
        if type(apps) is list:
            apps = apps[0]
        self.ws = connect("%s&app=%s" % (self.build_url("events").replace("http", "ws"), apps))
        for message in self.ws:
            try:
                event = json.loads(message)
                logging.debug(f"Received: {event}")

                channel_id = event.get('channel', {}).get('id')
                if not channel_id:
                    continue # FIXME
                channel = self.get_object(Channel, channel_id)

                if event['type'] in self.events:
                    self.events[event['type']](channel, event)
                if event['type'] in channel.events:
                    channel.events[event['type']](channel, event)

            except Exception:
                logging.exception("Exception on message %s" % (message))
                
