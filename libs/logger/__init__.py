import logging
from config import cfg



class CustomFormatter(logging.Formatter):

    logging.CHECK = 10
    logging.addLevelName(logging.CHECK, "CHECK")
    grey = "\x1b[38;20m"
    green= "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    blue = "\x1b[1;34m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(message)s  \n(%(pathname)s:%(lineno)d ->  %(funcName)s)"

    FORMATS = {
        logging.DEBUG: grey+ "⚪  " + format + reset,
        logging.INFO: blue+ "ℹ️  " + format + reset,
        logging.CHECK: green + "✅  " + format + reset,
        logging.WARNING: yellow+ "🟡  " + format + reset,
        logging.ERROR: red + "❌  " + format + reset,
        logging.CRITICAL: bold_red + "⛔  " + format + reset,
    }
    
    

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
level= cfg['logging']['level']
logger = logging.getLogger('pet-finder')
logger.setLevel(level)
logger.check = lambda msg, *args: logger._log(logging.CHECK, msg, args)
ch = logging.StreamHandler()
ch.setLevel(level)
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)