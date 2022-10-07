import os
from dotenv import load_dotenv
from datetime import datetime
import logging

DATE_START = datetime.now()

class ColorLogFormatter(logging.Formatter):

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    green = '\033[32m'
    reset = '\x1b[0m'
    
    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.green + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)



BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

PATH_DIR_LOGS = os.path.join(BASE_DIR, 'logs')

DEBUG = os.getenv('DEBUG') if os.getenv('DEBUG') is not None else False
FAKE = os.getenv('FAKE') if os.getenv('FAKE') is not None else False

WS_BROKER_HOST = os.getenv('WS_BROKER_HOST') if os.getenv('WS_BROKER_HOST') is not None else 'localhost'
WS_BROKER_QUEUE = os.getenv('WS_BROKER_QUEUE') if os.getenv('WS_BROKER_QUEUE') is not None else 'ws_berezka'

BEREZKA_TOKEN = os.getenv('BEREZKA_TOKEN')
BEREZKA_EXT_SYSTEM = os.getenv('BEREZKA_EXT_SYSTEM')
BEREZKA_ORDER_ID = os.getenv('BEREZKA_ORDER_ID')
BEREZKA_PRICE = os.getenv('BEREZKA_PRICE')
INN_ROSIM = os.getenv('INN_ROSIM')
KOD_SERVICE = os.getenv('KOD_SERVICE')

SUPPLIER = {
            'name':os.getenv('SUPPLIER_NAME'),
            'inn':os.getenv('SUPPLIER_INN'),
            'kpp':os.getenv('SUPPLIER_KPP'),
            'ogrn':os.getenv('SUPPLIER_OGRN'),
            'email':os.getenv('SUPPLIER_EMAIL'),
            'phone':os.getenv('SUPPLIER_PHONE'),
}

FILTER_ORDER_NUMBER = '10001497512' # краснодар
# FILTER_ORDER_NUMBER = '10015231112' # ростов
# FILTER_ORDER_NUMBER = '10042881212' # крым

FILTER_ORDER_TEXT = ('арест', 'имуществ', 'реализ')