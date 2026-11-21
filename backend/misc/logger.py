import logging
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path


_chat_session_id = ContextVar("chat_session_id", default="-")


def _add_chat_session(record: logging.LogRecord) -> bool:
    record.session_id = _chat_session_id.get()
    return True


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addFilter(_add_chat_session)

file_handler = logging.FileHandler(
    Path(__file__).with_name("rag.log"), encoding="utf-8", delay=True
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(filename)s:%(lineno)d [%(levelname)s] "
    "session_id=%(session_id)s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
))
logger.addHandler(file_handler)


@contextmanager
def log_chat_session(session_id):
    token = _chat_session_id.set(str(session_id))
    try:
        yield
    finally:
        _chat_session_id.reset(token)
