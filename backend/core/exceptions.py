from rest_framework.views import exception_handler


def onside_exception_handler(exc, context):
    """Wraps DRF's default handler so every error response has a
    consistent {"detail": ..., "code": ...} shape for the frontend/bot/app
    clients to branch on without inspecting field-specific keys."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data.setdefault("code", exc.__class__.__name__)
    return response
