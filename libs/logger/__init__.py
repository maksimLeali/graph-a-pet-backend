import logging
from config import cfg
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    green= "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(message)s  | %(name)s | %(levelname)s | %(asctime)s \n(%(pathname)s%(funcName)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
level= cfg['logging']['level']
logger = logging.getLogger('pet-finder')
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)