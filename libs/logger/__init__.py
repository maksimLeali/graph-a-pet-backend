import logging
from config import cfg
from json import dumps
from pydash import map_
import pathlib
import re


class CustomFormatter(logging.Formatter):    
    logging.CHECK = logging.INFO +5
    logging.INPUT = logging.DEBUG + 1
    logging.OUTPUT = logging.DEBUG  + 2
    logging.addLevelName(logging.CHECK, "CHECK")
    logging.addLevelName(logging.INPUT, "INPUT")
    logging.addLevelName(logging.OUTPUT, "OUTPUT")
    grey = "\x1b[38;20m"
    green= "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    blue = "\u001b[36m"
    bold_red = "\x1b[31;1m"
    purple = "\x1b[1;35m"
    reset = "\x1b[0m"
    format = "%(asctime)s %(levelname)s: §-§%(pathname)s§-§ |  %(funcName)s \n%(message)s\n "
    input_format = "%(levelname)s \n%(message)s \n"
    output_format = "%(message)s \n%(levelname)s \n"
    extended_format = "%(asctime)s %(levelname)s: %(message)s  \n(%(pathname)s:%(lineno)d ->  %(funcName)s)\n"

    FORMATS = {
        logging.DEBUG: grey+ "⚪  " + format + reset, #10
        logging.INPUT: purple + "🔻\n " + format + reset, #11
        logging.OUTPUT: purple + format + "🔺  \n" + reset, #12
        logging.INFO: blue+ "ℹ️  " + format + reset, #20
        logging.CHECK: green + "✅  " + format + reset, #25
        logging.WARNING: yellow + "🟡  " + extended_format + reset, #30
        logging.ERROR: red + "❌  " + extended_format + reset, #40
        logging.CRITICAL: bold_red + "⛔  " + extended_format + reset, #50
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%dT%H:%M:%S.00Z")
        formatted_record = re.sub(f"{str(pathlib.Path().resolve())}".replace('\\','/'), '',  formatter.format(record) )

        return re.sub("(§-§.*§-§)", format_path(re.search('(§-§.*§-§)'.replace('\\', '/'), formatted_record).group(0)), formatted_record ).replace("§-§","")
    
level= cfg['logging']['level']
logger = logging.getLogger('pet-finder')
logger.check = lambda msg, *args: logger._log(logging.CHECK, msg, args)
logger.input = lambda msg, *args: logger._log(logging.INPUT, msg, args)
logger.output = lambda msg, *args: logger._log(logging.OUTPUT, msg, args)
logger.setLevel(level)
ch = logging.StreamHandler()

ch.setLevel(level)
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)

def stringify(obj: dict)-> str:
    return dumps(obj, separators=(',',':'), indent=2)

def format_path(path):
    parts = re.sub(f"{str(pathlib.Path().resolve())}\\".replace('\\','/'), '', str(path.replace('\\', '/'))).split('/')
    to_return = f"{' | '.join(map_(parts, lambda part, i: part.upper() if(i < len(parts) -1) else part.lower()))} "
    return to_return