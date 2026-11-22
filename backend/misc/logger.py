import logging
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from uuid import UUID


_chat_session_id = ContextVar("chat_session_id", default="-")
log_folder = Path(__file__).resolve().parent / "logs"


def _add_chat_session(record: logging.LogRecord) -> bool:
    record.session_id = _chat_session_id.get()
    return True


class SessionFileHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.session_id == "-":
                filename = "rag.log"
            else:
                filename = f"{UUID(record.session_id)}.log"

            log_folder.mkdir(parents=True, exist_ok=True)
            with (log_folder / filename).open("a", encoding="utf-8") as file:
                file.write(self.format(record) + "\n")
        except Exception:
            self.handleError(record)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addFilter(_add_chat_session)

file_handler = SessionFileHandler()
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
