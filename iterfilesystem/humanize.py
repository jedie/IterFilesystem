def human_time(t):
    """
    >>> human_time(1.5)
    '1.5sec'

    >>> human_time(61)
    '1.0min'

    >>> human_time(3600)
    '60.0min'
    """
    if t > 3600:
        divisor = 3600.0
        unit = 'h'
    elif t > 60:
        divisor = 60.0
        unit = 'min'
    else:
        divisor = 1
        unit = 'sec'

    return f'{round(t / divisor, 2):.1f}{unit}'


def human_filesize(bytes):
    """
    'human-readable' file size:

    >>> human_filesize(0)
    '0 Byte'
    >>> human_filesize(1)
    '1 Byte'
    >>> human_filesize(2)
    '2 Bytes'
    >>> human_filesize(1023)
    '1023 Bytes'
    >>> human_filesize(1024)
    '1.0 KB'
    >>> human_filesize(1.5 * 1024 * 1024)
    '1.5 MB'
    >>> human_filesize(2.75 * 1024 * 1024 * 1024)
    '2.8 GB'
    """
    if bytes < 1024:
        return f'{bytes} Byte{bytes>1 and "s" or ""}'
    bytes = float(bytes)
    if bytes < 1024 * 1024:
        return '%.1f KB' % (bytes / 1024)
    if bytes < 1024 * 1024 * 1024:
        return '%.1f MB' % (bytes / (1024 * 1024))
    return '%.1f GB' % (bytes / (1024 * 1024 * 1024))
