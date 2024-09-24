import contextvars
from contextlib import contextmanager

session_var = contextvars.ContextVar('session', default=None)

@contextmanager
def set_session(session):
    token = session_var.set(session)
    try:
        yield session_var.get()
    finally:
        session_var.reset(token)
