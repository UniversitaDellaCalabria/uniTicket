from functools import wraps


def disable_for_loaddata(signal_handler):
    """Turn off a signal handler when loading fixture data.

    loaddata saves objects with raw=True: without this check a handler
    would create again objects already in the fixture (e.g. the default
    office of a structure).

    Args:
        signal_handler: The signal handler function to wrap.

    Returns:
        The wrapped handler, which does nothing when kwargs['raw'] is True.
    """
    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)
    return wrapper
