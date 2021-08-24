from contextlib import contextmanager

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest


def add_session_middleware(request: WSGIRequest):
    """Add session middleware to request"""
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    return request


def add_message_middleware(request: WSGIRequest):
    """Add message middleware to request"""
    middleware = MessageMiddleware()
    middleware.process_request(request)
    request.session.save()
    return request


@contextmanager
def does_not_raise():
    yield
