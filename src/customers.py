import logging

import pika, sys, os
from .config import WS_BROKER_HOST, WS_BROKER_QUEUE, DATE_START, PATH_DIR_LOGS, ColorLogFormatter, DEBUG, FILTER_ORDER_NUMBER, FILTER_ORDER_TEXT,FAKE
from .berezka_api import find_order_by_number, send_proposal
import json

logger = logging.getLogger('berezka-api-customer')
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_format = ColorLogFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

f_handler = logging.FileHandler(os.path.join(PATH_DIR_LOGS, f'berezka-api-customer-{DATE_START}.log'))
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_handler.setFormatter(f_format)
f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)

if DEBUG:
    c_handler.setLevel(logging.DEBUG)
else:
    c_handler.setLevel(logging.INFO)

def filterOrderNumber(order_number):
    return FILTER_ORDER_NUMBER in order_number

def filterOrderName(order_name):
    return all(map(lambda x: x in order_name,FILTER_ORDER_TEXT))

def ws_callback(ch, method, properties, body):
        try:
            logger.info(f'Получили сообщение из очереди - > {WS_BROKER_QUEUE}, данные -> {body}')
            order_json = json.loads(body.decode('utf-8'))

            order_number = order_json.get('order','')
            logger.debug(f'Попытка получить информацию и конкурсе на сайте березка')
            logger.warning(f'Фильтрация по номеру {order_number}')
            if not filterOrderNumber(order_number):
                logger.debug(f'Конкурс не прошел фильтрацию по номеру. Выходим из функции')
                return False
            else:
                logger.debug(f'Конкурс прошел фильтрацию по номеру. Выполняем проверку дальше')
            logger.debug(f'Попытка запросить конкурс у berezka')
            order_json = find_order_by_number(order_number)
            logger.debug(f'Информация получена -> {order_json}')
            if not filterOrderName(order_json["items"][0]["product"][0]["name"]):
                logger.debug(f'Конкурс не прошел фильтрацию по тексту. Выходим из функции')
                return False
            else:
                logger.debug(f'Конкурс прошел фильтрацию по тексту. Переходим к подаче предложения')
            logger.debug(f'Попытка отправить предложение по конкурсу')
            result_proposal = send_proposal(order_json, fake=FAKE)
            logger.debug(f'Результат отправки  предложение {result_proposal}')
            
            return True
        except Exception as ex:
            return False

def _ws_customer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=WS_BROKER_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=WS_BROKER_QUEUE)

    channel.basic_consume(queue=WS_BROKER_QUEUE, on_message_callback=ws_callback, auto_ack=True)
    channel.start_consuming()

def ws_customer():
    try:
        _ws_customer()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__':
    # logger.info('Тестовое сообщение')
    pass