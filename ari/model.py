import requests
import time

class Repository:
    def __init__(self, client, contains):
        self.client = client
        self.contains = contains

    def list(self):
        l = []
        r = requests.get(self.client.build_url(self.contains.API))
        r.raise_for_status()
        for data in r.json():
            obj_id = data.get("id")
            if not obj_id:
                continue
            obj = self.client.get_object(self.contains, obj_id)
            obj.update(data)
            l.append(obj)
        return l

    def create(self, **kvargs):
        r = requests.post(self.client.build_url(self.contains.API), data=kvargs)
        r.raise_for_status()
        data = r.json()
        obj_id = data.get("id")
        if not obj_id:
            return None
        obj = self.client.get_object(self.contains, obj_id)
        obj.update(data)
        return obj

    def originate(self, **kvargs):  # Alias for Channel
        if "app" not in kvargs:
            kvargs["app"] = self.client.appname
        return self.create(**kvargs)


class BaseObject:
    KEY = None
    API = None

    def __init__(self, client, id=None, json={}):
        self.client = client
        self.id = id
        self.last_update = None
        if json:
            self.update(json)
        self.events = {}

    def __str__(self):
        return "<ARI %s %s>"%(self.__class__.__name__, self.id)

    def __repr__(self):
        return "<ARI %s %s at 0x%x>"%(self.__class__.__name__, self.id, id(self))

    def on_event(self, event_type, callback):
        self.events[event_type] = callback

    def update(self, json):
        self.json = json
        self.last_update = time.time()
        if json and not self.id:
            self.id = json.get('id')

    def get(self):
        r = requests.get(self.client.build_url("/".join([self.API, self.id])))
        r.raise_for_status()
        self.json = r.json()
        return self.json

    def delete(self):
        r = requests.delete(self.client.build_url("/".join([self.API, self.id])))
        r.raise_for_status()
        #self.client.del_object(self)  # Last events after this one recreates the object

    def __getattr__(self, name):
        def call(*args, **kvargs):
            for k in kvargs:
                if type(kvargs[k]) is list:
                    kvargs[k] = ",".join(kvargs[k])
            r = requests.post(self.client.build_url("/".join([self.API, self.id, name.lstrip("_")])), data=kvargs)
            r.raise_for_status()
            if r.status_code == 204:
                return None
            else:
                return r.json()
        return call


class Endpoint(BaseObject):
    KEY = "endpoint"
    API = "endpoints"


class Bridge(BaseObject):
    KEY = "bridge"
    API = "bridges"

    def destroy(self):
        self.delete()


class Channel(BaseObject):
    KEY = "channel"
    API = "channels"
    
    def hangup(self):
        self.delete()

    def hang_up(self):
        self.delete()

    def continueInDialplan(self):
        self._continue()

    def play(self, **kvargs):
        r = self.__getattr__('play')(**kvargs)
        obj = self.client.get_object(Playback, r['id'])
        obj.update(r)
        return obj


class Recording(BaseObject):
    KEY = "recording"
    API = "recordings"


class Sound(BaseObject):
    KEY = "sound"
    API = "sounds"


class Playback(BaseObject):
    KEY = "playback"
    API = "playbacks"

    def stop(self):
        self.delete()


ALL_MODELS = [
    Channel,
    Bridge
]
