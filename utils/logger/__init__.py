from __future__ import annotations

import logging
import pathlib
import sys
from json import dumps
from config import cfg

# ---------------------------------------------------------------------------
# Custom level registration (must happen before any logger is configured)
# ---------------------------------------------------------------------------
_CUSTOM_LEVELS: dict[str, int] = {
    "INPUT":      logging.DEBUG + 1,   # 11
    "OUTPUT":     logging.DEBUG + 2,   # 12
    "MIDDLEWARE": logging.INFO  + 1,   # 21
    "API":        logging.INFO  + 2,   # 22
    "DOMAIN":     logging.INFO  + 3,   # 23
    "REPOSITORY": logging.INFO  + 4,   # 24
    "CHECK":      logging.INFO  + 5,   # 25
    "START":      logging.INFO  + 6,   # 26
    "SETUP":      logging.ERROR + 1,   # 41
}

for _name, _value in _CUSTOM_LEVELS.items():
    logging.addLevelName(_value, _name)
    setattr(logging, _name, _value)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
# Resolve the project root from this file's location: utils/logger/__init__.py
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

def _format_path(pathname: str) -> str:
    """Return a readable 'FOLDER | FOLDER | file.py' string from an absolute path."""
    try:
        rel = pathlib.Path(pathname).resolve().relative_to(_PROJECT_ROOT)
    except ValueError:
        rel = pathlib.Path(pathname).name  # fallback: just the filename
        return str(rel)
    parts = rel.parts
    segments = [p.upper() for p in parts[:-1]] + [parts[-1].lower()]
    return " | ".join(segments)

def _relative_path(pathname: str) -> str:
    """Return the project-relative posix path, all lowercase, no spaces."""
    try:
        rel = pathlib.Path(pathname).resolve().relative_to(_PROJECT_ROOT)
        return rel.as_posix().lower()
    except ValueError:
        return pathlib.Path(pathname).name.lower()

# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
class CustomFormatter(logging.Formatter):
    _reset       = "\x1b[0m"
    _italic      = "\x1b[3m"
    _grey        = "\x1b[38;20m"
    _green       = "\033[92m"
    _yellow      = "\x1b[33;20m"
    _red         = "\x1b[31;20m"
    _bold_red    = "\x1b[31;1m"
    _purple      = "\x1b[1;35m"
    _yellow_bold = "\033[1;33m"
    _blue        = "\u001b[36m"
    _blue_bold   = "\033[1;34m"
    _green_bold  = "\033[1;32m"
    _cyan_bold   = "\033[1;36m"

    _BASE_FMT     = "%(asctime)s %(levelname)s: %(pathname)s | %(funcName)s()" + _reset + "\n%(message)s\n"
    _EXTENDED_FMT = _BASE_FMT + _italic + "[ %(relpath)s:%(lineno)d ]\n"
    _START_FMT    = "%(message)s"

    _FORMATS = {
        logging.DEBUG:      _grey        + "⚪  " + _BASE_FMT       + _reset,  # 10
        logging.INPUT:      _purple      + "🔻\n " + _BASE_FMT      + _reset,  # 11
        logging.OUTPUT:     _purple      + _BASE_FMT + "🔺  \n"     + _reset,  # 12
        logging.INFO:       _blue        + "ℹ️  "  + _EXTENDED_FMT  + _reset,  # 20
        logging.MIDDLEWARE: _yellow_bold + "🔑  "  + _EXTENDED_FMT  + _reset,  # 21
        logging.API:        _green_bold  + "📤  "  + _EXTENDED_FMT  + _reset,  # 22
        logging.DOMAIN:     _cyan_bold   + "🛠️  "  + _EXTENDED_FMT  + _reset,  # 23
        logging.REPOSITORY: _blue_bold   + "📁  "  + _EXTENDED_FMT  + _reset,  # 24
        logging.CHECK:      _green       + "✅  "  + _EXTENDED_FMT  + _reset,  # 25
        logging.START:      _italic + _green_bold + "🚀  " + _START_FMT + _reset,  # 26
        logging.SETUP:      _italic + _cyan_bold  + "⚙️  " + _START_FMT + _reset,  # 41
        logging.WARNING:    _yellow      + "🟡  "  + _EXTENDED_FMT  + _reset,  # 30
        logging.ERROR:      _red         + "❌  "  + _EXTENDED_FMT  + _reset,  # 40
        logging.CRITICAL:   _bold_red    + "⛔  "  + _EXTENDED_FMT  + _reset,  # 50
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = self._FORMATS.get(record.levelno, self._BASE_FMT)
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S")
        # Work on a shallow copy so we never mutate the original record
        copy = logging.makeLogRecord(record.__dict__)
        copy.relpath = _relative_path(record.pathname)
        copy.pathname = _format_path(record.pathname)
        return formatter.format(copy)

# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------
_py_version  = (sys.version_info.major, sys.version_info.minor)
_stack_level = 2 if _py_version >= (3, 9) else 1

def _build_logger(name: str, level: str) -> logging.Logger:
    log = logging.getLogger(name)
    log.propagate = False  # prevent double-output via root logger
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(CustomFormatter())
        log.addHandler(handler)
    log.setLevel(level)
    return log

_level = cfg["logging"]["level"]
logger = _build_logger("graph-a-pet", _level)

# Attach custom level helpers directly to the logger instance
logger.check      = lambda msg, *args: logger._log(logging.CHECK,      msg, args, stacklevel=_stack_level)
logger.input      = lambda msg, *args: logger._log(logging.INPUT,      msg, args, stacklevel=_stack_level)
logger.output     = lambda msg, *args: logger._log(logging.OUTPUT,     msg, args, stacklevel=_stack_level)
logger.middleware = lambda msg, *args: logger._log(logging.MIDDLEWARE,  msg, args, stacklevel=_stack_level)
logger.api        = lambda msg, *args: logger._log(logging.API,        msg, args, stacklevel=_stack_level)
logger.domain     = lambda msg, *args: logger._log(logging.DOMAIN,     msg, args, stacklevel=_stack_level)
logger.repository = lambda msg, *args: logger._log(logging.REPOSITORY, msg, args, stacklevel=_stack_level)
logger.start      = lambda msg, *args: logger._log(logging.START,      msg, args, stacklevel=_stack_level)
logger.setup      = lambda msg, *args: logger._log(logging.SETUP,      msg, args, stacklevel=_stack_level)

logger.setup(f"python {_py_version[0]}.{_py_version[1]} | stacklevel: {_stack_level}")

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def stringify(obj: dict) -> str:
    return dumps(obj, separators=(",", ":"), indent=2)