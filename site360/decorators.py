import functools
from .utils import log_response_action

def user_action_logging(view_func):
    """
    Decorator to log user actions in Function Based Views
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        log_response_action(request, response)
        return response
    return wrapper
