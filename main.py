import logging
import os
from src.config import DATE_START, PATH_DIR_LOGS, ColorLogFormatter, DEBUG

logger = logging.getLogger('api-berezka')
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_format = ColorLogFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

f_handler = logging.FileHandler(os.path.join(PATH_DIR_LOGS, f'api-berezka-{DATE_START}.log'))
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_handler.setFormatter(f_format)
f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)

if DEBUG:
    c_handler.setLevel(logging.DEBUG)
else:
    c_handler.setLevel(logging.INFO)


from src.customers import ws_callback, ws_customer
# from src.config import FAKE, DEBUG
store = (
    # ('100014975122100014',False),
    ('100014975122100013',True),
    # ('100014975122100010',False),
    # ('100014975121100059',True),
    # ('100152311122100061', False)
)


def test_root():
    for i in store:
        result = ws_callback(None, None, None, i[0].encode('utf-8'))
        assert result == i[-1]
        print('все оk')


if __name__ == '__main__':
    # test_root()
    print('starting ws_customer')
    ws_customer()
    # print(FAKE)
    # print(type(FAKE))