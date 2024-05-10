import logging
from config import cfg
from json import dumps
from pydash import map_
import pathlib
import re
import sys

# Get the major and minor version of Python
major_version = sys.version_info.major
minor_version = sys.version_info.minor

class CustomFormatter(logging.Formatter):    
    # DEBUG: 10, 
    logging.INPUT = logging.DEBUG + 1  # Level 11
    logging.OUTPUT = logging.DEBUG + 2  # Level 12
    #INFO: 20, 
    logging.MIDDLEWARE = logging.INFO + 1  # Level 21
    logging.API = logging.INFO + 2  # Level 22
    logging.DOMAIN = logging.INFO + 3  # Level 23
    logging.REPOSITORY = logging.INFO + 4  # Level 24
    logging.CHECK = logging.INFO + 5  # Level 25
    logging.START = logging.INFO + 6  # Level 26
    #WARNING: 30, 
    #ERROR: 40, 
    logging.SETUP = logging.ERROR + 1  # Level 41
    #CRITICAL: 50
    logging.addLevelName(logging.INPUT, "INPUT")
    logging.addLevelName(logging.OUTPUT, "OUTPUT")
    logging.addLevelName(logging.MIDDLEWARE, "MIDDLEWARE")
    logging.addLevelName(logging.API, "API")
    logging.addLevelName(logging.DOMAIN, "DOMAIN")
    logging.addLevelName(logging.REPOSITORY, "REPOSITORY")
    logging.addLevelName(logging.CHECK, "CHECK")
    logging.addLevelName(logging.START, "START")
    logging.addLevelName(logging.SETUP, "SETUP")
    grey = "\x1b[38;20m"
    green= "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    blue = "\u001b[36m"
    bold_red = "\x1b[31;1m"
    purple = "\x1b[1;35m"
    yellow_bold= "\033[1;33m"
    blue_bold = "\033[1;34m"
    green_bold = "\033[1;32m"
    cyan_bold = "\033[1;36m" 
    reset = "\x1b[0m"
    italic= "\x1b[3m"
    format = "%(asctime)s %(levelname)s: §-§%(pathname)s§-§ | %(funcName)s()" + reset + "\n%(message)s\n"
    extended_format = format +italic +"[ %(pathname)s:%(lineno)d ]\n"
    start_format =  "%(message)s"

    FORMATS = {
        logging.DEBUG: grey+ "⚪  " + format + reset, #10
        logging.INPUT: purple + "🔻\n " + format + reset, #11
        logging.OUTPUT: purple + format + "🔺  \n" + reset, #12
        logging.INFO: blue+ "ℹ️  " + extended_format + reset, #20
        logging.MIDDLEWARE: yellow_bold + "🔑  " + extended_format + reset, #21
        logging.API: green_bold + "📤  " + extended_format + reset, #22
        logging.DOMAIN: cyan_bold + "🛠️  " + extended_format + reset, #23
        logging.REPOSITORY: blue_bold + "📁  " + extended_format + reset, #24
        logging.CHECK: green + "✅  " + extended_format + reset, #25
        logging.START:italic + green_bold + "🚀  "  + start_format + reset, #26
        logging.SETUP:italic + cyan_bold + "⚙️  "  + start_format + reset, #41
        logging.WARNING: yellow + "🟡  " + extended_format + reset, #30
        logging.ERROR: red + "❌  " + extended_format + reset, #40
        logging.CRITICAL: bold_red + "⛔  " + extended_format + reset, #50
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%dT%H:%M:%S.%fZ.00Z")
        if (record.levelno in [logging.START, logging.SETUP]):
            return formatter.format(record)
        formatted_record = re.sub(f"{str(pathlib.Path().resolve())}/".replace('\\','/'), '',  formatter.format(record) )

        return re.sub("(§-§.*§-§)", format_path(re.search('(§-§.*§-§)'.replace('\\', '/'), formatted_record).group(0)), formatted_record ).replace("§-§","") 
    
level= cfg['logging']['level']
logger = logging.getLogger('waitress')
stackLevelPerPyVersion = 2 if (major_version, minor_version) >= (3, 9) else 1

print(f'python version:{(major_version, minor_version) } stacklevekl : {stackLevelPerPyVersion}')
logger.check = lambda msg, *args: logger._log(logging.CHECK, msg, args, stacklevel=stackLevelPerPyVersion)
logger.input = lambda msg, *args: logger._log(logging.INPUT, msg, args, stacklevel=stackLevelPerPyVersion)
logger.output = lambda msg, *args: logger._log(logging.OUTPUT, msg, args, stacklevel=stackLevelPerPyVersion)
logger.middleware = lambda msg, *args: logger._log(logging.MIDDLEWARE, msg, args, stacklevel=stackLevelPerPyVersion)
logger.api = lambda msg, *args: logger._log(logging.API, msg, args, stacklevel=stackLevelPerPyVersion)
logger.domain = lambda msg, *args: logger._log(logging.DOMAIN, msg, args, stacklevel=stackLevelPerPyVersion)
logger.repository = lambda msg, *args: logger._log(logging.REPOSITORY, msg, args, stacklevel=stackLevelPerPyVersion)
logger.start = lambda msg, *args: logger._log(logging.START, msg, args, stacklevel=stackLevelPerPyVersion)
logger.setup = lambda msg, *args: logger._log(logging.SETUP, msg, args, stacklevel=stackLevelPerPyVersion)
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