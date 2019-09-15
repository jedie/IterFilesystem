import base64
import hashlib


def left_shorten(text, width=30, placeholder='...'):
    """
    >>> left_shorten('alongstring', width=8, placeholder='..')
    '..string'

    >>> left_shorten('1234567890', width=12)
    '  1234567890'
    """
    if len(text) > width:
        width -= len(placeholder)
        return f'{placeholder}{text[-width:]}'
    else:
        return f'{text:>{width}}'


def string2hash(text):
    """
    >>> string2hash(text='foobar')
    'ClAmH'
    """
    h = hashlib.sha512()
    h.update(bytes(text, encoding='UTF-8'))
    base64_bytes = base64.b64encode(h.digest())[:5]
    return base64_bytes.decode('UTF-8')
