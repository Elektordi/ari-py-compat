import requests

class BaseObject:
    API = "asterisk"

    def __init__(self, client, id=None):
        self.client = client
        self.id = id
        self.events = {}

    def on_event(self, event_type, callback):
        self.events[event_type] = callback

    def get(self):
        r = requests.get(self.build_url(self.API))
        r.raise_for_status()
        return r.json()

    def delete(self):
        r = requests.delete(self.client.build_url("/".join([self.API, self.id])))
        r.raise_for_status()
        self.client.del_object(self)

    def __getattr__(self, name):
        def call(*args, **kvargs):
            r = requests.post(self.client.build_url("/".join([self.API, self.id, name])), data=kvargs)
            r.raise_for_status()
            if r.status_code == 204:
                return None
            else:
                return r.json()
        return call

class Channel(BaseObject):
    API = "channels"
    
    def hang_up(self):
        self.delete()
