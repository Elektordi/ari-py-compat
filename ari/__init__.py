from .client import Client


def connect(url, username, password):
    c = Client(url, username, password)
    c.connect()
    return c

