from .client import Client


def connect(*args, **kvargs):
    c = Client(*args, **kvargs)
    c.connect()
    return c

