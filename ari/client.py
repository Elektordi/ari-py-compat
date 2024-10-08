import requests
import json
from websockets.sync.client import connect
import logging
from concurrent.futures import ThreadPoolExecutor
import time

from .model import Channel, Bridge, Repository, ALL_MODELS


log = logging.getLogger("ari")


class Client:
    def __init__(self, url, username, password, max_workers=None, cleanup_interval=300, cleanup_age=3600):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.max_workers = max_workers
        self.cleanup_interval = cleanup_interval
        self.cleanup_age = cleanup_age

        self.appname = None
        self.ws = None
        self.events = {}
        self.objects = {}
        self.executor = None
        self.running = True
        self.next_cleanup = time.time() + self.cleanup_interval

        self.channels = Repository(self, Channel)
        self.bridges = Repository(self, Bridge)

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

    def cleanup(self):
        try:
            log.debug("Starting cleanup")
            deadline = time.time() - self.cleanup_age
            for key, obj in list(self.objects.items()):
                if obj.last_update < deadline:
                    del self.objects[key]
                    log.debug("Cleared %r" % (obj))
            log.debug("Finished cleanup")
        except Exception:
            log.exception("Exception during ARI cleanup")

    def connect(self):
        r = requests.get(self.build_url("api-docs/resources.json"))
        r.raise_for_status()
        assert len(r.json()["apis"]) > 0

    def on_channel_event(self, event_type, callback):
        self.events[event_type] = callback

    def _callback(self, callback, obj, event):
        def _wrapper(callback, obj, event):
            try:
                callback(obj, event)
            except Exception as ex:
                log.exception("Exception on callback %s, event was %s" % (callback, event))
                if isinstance(ex, requests.exceptions.HTTPError):
                    log.debug("Exception body was: %s" % (ex.response.text))
        self.executor.submit(_wrapper, callback, obj, event)

    def run(self, apps="no-name", reconnect=True):
        if type(apps) is list:
            apps = apps[0]
        self.appname = apps
        while reconnect and self.running:
            try:
                self.ws = connect("%s&app=%s" % (self.build_url("events").replace("http", "ws"), apps))
                self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="ari_callback")
                for message in self.ws:
                    try:
                        event = json.loads(message)
                        log.debug(f"Received: {event}")

                        for model in ALL_MODELS:
                            if model.KEY not in event:
                                continue
                            obj_id = event[model.KEY].get("id")
                            if not obj_id:
                                continue
                            obj = self.get_object(model, obj_id)
                            obj.update(event[model.KEY])

                            if event['type'] in obj.events:
                                self._callback(obj.events[event['type']], obj, event)

                            if model is Channel:
                                if event['type'] in self.events:
                                    self._callback(self.events[event['type']], obj, event)

                    except Exception:
                        log.exception("Exception on message %s" % (message))

                    if self.next_cleanup < time.time():
                        self.next_cleanup = time.time() + self.cleanup_interval
                        self.executor.submit(self.cleanup)

            except Exception:
                if self.running:
                    log.exception("Exception on ARI main loop")
                    time.sleep(1)  # Prevents DoS on server
            finally:
                self.executor.shutdown(wait=True, cancel_futures=True)
                self.ws.close()

    def close(self):
        self.running = False
        self.ws.close()

