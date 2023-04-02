import traceback

def print_traceback(f):
    """
    A decorator to display exception trace, because Sphinx hides them for
    some reason...
    """
    def wrapped(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as err:
            print(traceback.format_exc())
            raise err
    return wrapped
