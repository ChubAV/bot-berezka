import logging

import pika, sys, os
from .config import WS_BROKER_HOST, WS_BROKER_QUEUE, FILTER_ORDER_NUMBER, FILTER_ORDER_TEXT,FAKE, EMAIL_ADMIN, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, EMAIL_RECIPIENT 
from .berezka_api import find_order_by_number, send_proposal
import json
from notifications import Mail

logger = logging.getLogger('api-berezka')

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
            
            try:
                mail = Mail(SMTP_SERVER, SMTP_PORT, EMAIL_ADMIN, EMAIL_PASSWORD)
                mail.send([EMAIL_RECIPIENT,], 'Березка - Отправка предложения', f'Отправка предложения по конкурсу {order_number}')
            except Exception as ex:
                pass
            
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