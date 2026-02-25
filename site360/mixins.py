from .utils import log_response_action

class UserActionLoggingMixin:
    """
    Mixin to log user actions in Class Based Views
    """
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        log_response_action(request, response)
        return response
