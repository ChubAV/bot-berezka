import logging
import os
from .config import  BEREZKA_TOKEN, BEREZKA_EXT_SYSTEM, BEREZKA_PRICE, SUPPLIER
import requests
from requests.exceptions import RequestException
import uuid
from datetime import time
import time

logger = logging.getLogger('api-berezka')

class ExceptionBerezkaNot200(Exception):
    pass

class ExceptionBerezkaNotFoundOrder(Exception):
    pass

class ExceptionBerezkaErrorProposal(Exception):
    pass

class requestBerezkaBase:
    
    def __init__(self, token, ext_system):
        self.GUID = self._genGUID()
        self.ext_system = ext_system
        self.token = token
        self.url_result = 'https://agregatoreat.ru/integration/ecom/rest/api/processingResult'
        self._getHeaders()
        self.url_request = ''
        self.message = ''
        self.setTimeOut(1)
    
    def _genGUID(self):
        self.GUID = str(uuid.uuid4())
        return  self.GUID
    
    def _getHeaders(self):
        self.headers = {
                    'Authorization': 'Bearer {}'.format(self.token),
                    'Content-Type': 'text/xml',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                    # 'cookie':'4WXMP4VOTVIxE8igNwIlvr7_WOs=nHZH5yvn9ihourq50Q9pjVHlKKs; BceMiZ1yceM6FB1EFjnkx-um7wo=IuiHcqbC-ui2Di8v8vywA-SqhEA; Jrdc6e5aT3un1-RCnOlau8C_ttM=qzSPEuiNUtg3lMFvfCW2hs5ssSQ; SQcxKOOF1AV3AqG8peeB_Igq978=1657538453; WV71eBG3DDtLp1ZDhmSry2BCves=1657545653; euWHYVCEprEgSJhB76H8P0ZWQOA=HmLukgDdDJ3fK4fU68rutsDL1Lo; ocpyDU4JYw6VgxgwH5WALR13P3g=1657538474; wkQs9UpxQ7DWERggi46y1i-sew8=1657545674'
                    }
        return self.headers
    
    def setTimeOut(self, time_out):
        self.time_out = time_out

    def _createMessage(self):
        pass

    def _createMessageResult(self):
        message = '<?xml version="1.0" encoding="UTF-8"?>' + \
                  '<n1:requestProcessingResult xmlns:eat="http://agregatoreat.ru/eat/" '+ \
                  'xmlns:n1="http://agregatoreat.ru/eat/object-types/" ' + \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
                  'eat:Version="2.0.0" eat:RequestUID="{}">' + \
	              '<extSystem>{}</extSystem>' + \
                  '</n1:requestProcessingResult>'
        return message.format(self.GUID, self.ext_system)     
    
    def _request(self, request_main = True):
       
        response = requests.post(self.url_request if request_main else self.url_result, 
                                 data = self.message.encode('utf-8') if request_main else self._createMessageResult().encode('utf-8'),
                                 headers = self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise ExceptionBerezkaNot200('Ошибка доступа к сервису код - {}'.format(response.status_code))    

    def _requestMain(self):
        
        return self._request()

    def _requestResult(self):
        result = {}
        count_iter = 1
        MAX_ERROR = 3
        count_error = 0
        while not (result.get('processingState', '') == 'complete'
                   or result.get('processingState', '') == 'error'):
            try:
                logger.debug(f'Запрос результатов обработки. Попытка - {count_iter}') 
                if count_iter == 1:
                    result = self._request(request_main = False)
                else:
                    logger.debug(f'Результаты основного запроса не готовы. Статус обработки - {result["processingState"]}. Пауза {max(self.time_out, 10)}')
                    time.sleep(max(self.time_out, 10)) # таймаут на обработку запроса на сервере по умолчанию 1 сек 
                    result = self._request(request_main = False)
                logger.debug(f'Ответ на запрос результатов обработки: {result}')
                count_iter += 1
            except Exception as ex:
                logger.exception(ex)
                # raise ex
                if count_error>=MAX_ERROR:
                    return {'processingState':'processing', 'processing':'Не получается получить результаты обработки'}
                else:
                    count_error += 1 
                    count_iter += 1

        return result
    
    def __call__(self):
        logger.debug(f'Тело основного запроса: {self.message}')
        
        result_main_request = self._requestMain() # если в этом блоке будет исключение тогда нет смысла продолжать
        
        logger.debug(f'Ответ сервера на основной запрос: {result_main_request}')
        
        time.sleep(self.time_out) # таймаут на обработку запроса на сервере по умолчанию 1 сек 
        
        logger.debug(f'Запрос результатов обработки: {self._createMessageResult()}')
        
        result = self._requestResult()
        
        # logger.debug(f'Ответ на запрос результатов обработки: {result}')

        return result

class requestBerezkaOrder(requestBerezkaBase):
    
    def __init__(self, token, ext_system, order_number):
        super().__init__(token, ext_system)
        self.url_request = 'https://agregatoreat.ru/integration/ecom/rest/api/order/orderNotification'
        self.order_number = order_number
        self._createMessage()
    
    def _createMessage(self):
        message = '<?xml version="1.0" encoding="UTF-8"?>' + \
                  '<n1:requestOrderNotification xmlns:eat="http://agregatoreat.ru/eat/" '+ \
                  'xmlns:n1="http://agregatoreat.ru/eat/object-types/" ' + \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
                  'eat:Version="2.0.0" eat:RequestUID="{}">'+ \
	                '<eat:OrderNumber>{}</eat:OrderNumber>' + \
	                '<extSystem>{}</extSystem>' + \
                   '</n1:requestOrderNotification>'
        self.message = message.format(self.GUID, self.order_number, self.ext_system)
        return self.message
    
    def __call__(self):
        result =  super().__call__()
        if result['items'] == None:
            raise ExceptionBerezkaNotFoundOrder('Закупка не найдена.') 
        elif result['items'][0]['orderNumber'] == self.order_number:
            return result
        else:
            raise ExceptionBerezkaNotFoundOrder('Закупка не найдена. Ответ сервера: \n {}'.format(str(result)))      



class requestBerezkaListOrder(requestBerezkaBase): 
    def __init__(self, token, ext_system):
        super().__init__(token, ext_system)
        self.url_request = 'https://agregatoreat.ru/integration/ecom/rest/api/order/requestOrderList'
        self._createMessage()
    
    def _createMessage(self):
        message ='<?xml version="1.0" encoding="UTF-8"?>'+ \
                '<n1:requestOrderList xmlns:eat="http://agregatoreat.ru/eat/" ' + \
                'xmlns:n1="http://agregatoreat.ru/eat/object-types/" ' + \
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' + \
                'eat:Version="2.0.0" eat:RequestUID="{}">' + \
	                  '<extSystem>{}</extSystem>' + \
                '</n1:requestOrderList>'
        self.message = message.format(self.GUID, self.ext_system)
        return self.message

class requestBerezkaProposal(requestBerezkaBase):
    def __init__(self, token, ext_system, order, price, supplier):
        super().__init__(token, ext_system)
        self.url_request = 'https://agregatoreat.ru/integration/ecom/rest/api/order/orderProposal'
        self.order = order
        self.price = price
        self.supplier = supplier
        self._createMessage()

    def _createMessage(self):
        message = '<?xml version="1.0" encoding="UTF-8"?>' + \
                  '<n1:requestOrderProposal xmlns:eat="http://agregatoreat.ru/eat/" ' + \
                  'xmlns:n1="http://agregatoreat.ru/eat/object-types/" ' + \
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        
        message += 'eat:Version="2.0.0" eat:RequestUID="{}"><referenceOrderInfo>'.format(self.GUID)
        
        message += '<eat:OrderNumber>{}</eat:OrderNumber>'.format(self.order['orderNumber'])
        message += '<eat:startDate>{}</eat:startDate>'.format(self.order['startDate'])
        message += '<eat:orderExpireDate>{}</eat:orderExpireDate>'.format(self.order['orderExpireDate'])
        message += '<eat:typePurchase>{}</eat:typePurchase>'.format(self.order['typePurchase'])
       
        message_offer = ''
        for product_json in self.order['product']:
            message += '<eat:Product>'
            message_offer += '<eat:productRef>'
            
            message += '<eat:sequenceNumber>{}</eat:sequenceNumber>'.format(product_json['sequenceNumber'])
            message_offer +='<eat:refSequenceNumber>{}</eat:refSequenceNumber>'.format(product_json['sequenceNumber'])

            message += '<eat:EATofferNumber>{}</eat:EATofferNumber>'.format(product_json['eaTofferNumber']) if not 'None' in str(product_json['eaTofferNumber']) else ''
            
            if not 'None' in str(product_json['eaTofferNumber']):
                    message_offer +='<eat:offerCode>{}</eat:offerCode>'.format(product_json['eaTofferNumber'])
            # else:
            #     print('это None')

            # message_offer +='<eat:offerCode>{}</eat:offerCode>'.format(product_json['eaTofferNumber']) if not 'None' in str(product_json['eaTofferNumber']) else '<eat:offerCode>300853720.000000005_19</eat:offerCode>'

            message += '<eat:EATClassifierRefCode>{}</eat:EATClassifierRefCode>'.format(product_json['eatClassifierRefCode'])
            message += '<eat:name>{}</eat:name>'.format(product_json['name'])
            message += '<eat:OKEI>' 
            message += '<eat:code>{}</eat:code>'.format(product_json['okei']['code'])
            message += '<eat:name>УСЛ ЕД</eat:name>'.format(product_json['okei']['name'])
            message += '</eat:OKEI>'
            message += '<eat:OKPD>' 
            message += '<eat:code>{}</eat:code>'.format(product_json['okpd']['code'])
            message += '<eat:name>{}</eat:name>'.format(product_json['okpd']['name'])
            message += '</eat:OKPD>'
            message += '<eat:availableVolume>{}</eat:availableVolume>'.format(product_json['availableVolume'])
            message += '<eat:homogeneousProductIsPossible>{}</eat:homogeneousProductIsPossible>'.format(str(product_json['homogeneousProductIsPossible']).lower())      
            message += '</eat:Product>'

            message_offer +='<eat:unitPrice>{}</eat:unitPrice>'.format(self.price)
            message_offer +='<eat:nds>{}</eat:nds>'.format('0')
            message_offer += '</eat:productRef>'

        
        message += '<eat:Customer>'
        message += '<eat:CustomerName>{}</eat:CustomerName>'.format(self.order['customer']['customerName'])
        message += '<eat:sellerRef>'
        message += '<eat:INN>{}</eat:INN>'.format(self.order['customer']['sellerRef']['items'][0])
        message += '<eat:KPP>{}</eat:KPP>'.format(self.order['customer']['sellerRef']['items'][1])
        message += '<eat:OGRN>0000000000000</eat:OGRN>'
        message += '</eat:sellerRef>'
        message += '</eat:Customer>'

        message += '<eat:maxOrderCost>{}</eat:maxOrderCost>'.format(str(self.order['maxOrderCost']).replace(',','').replace(' ',''))

        message += '<eat:PaymentDetails>'
        message += '<eat:PaymentType>{}</eat:PaymentType>'.format(self.order['paymentDetails']['paymentType'])
        message += '<eat:PaymentTerms>{}</eat:PaymentTerms>'.format(self.order['paymentDetails']['paymentTerms'])
        message += '<eat:PaymentDeadlineInterval>0</eat:PaymentDeadlineInterval>'
        message += '</eat:PaymentDetails>'

        message += '<eat:DeliveryDate>{}</eat:DeliveryDate>'.format(str(self.order['deliveryDate'])[:10])
        message += '<eat:remoteService>{}</eat:remoteService>'.format(str(self.order['remoteService']).lower())
        message += '<eat:WWWReference>{}</eat:WWWReference>'.format(self.order['wwwReference'])
        message += '<eat:planDateConclusion>{}</eat:planDateConclusion>'.format(str(self.order['planDateConclusion'])[:10])
        message += '<eat:gosoboronzakaz>{}</eat:gosoboronzakaz>'.format('Да' if self.order['gosoboronzakaz'] == 1 else 'Нет')
        message += '<eat:RNP44Flag>{}</eat:RNP44Flag>'.format('Да' if self.order['rnP44Flag'] == 1 else 'Нет')
        message += '<eat:state>{}</eat:state>'.format(self.order['state'])
        message += '<eat:stateDescription>{}</eat:stateDescription>'.format(self.order['stateDescription'])

        message += '</referenceOrderInfo><OrderProposalInfo>'
        
        message += message_offer
        
        message += '<eat:SupplierInfo>'
        message += '<eat:name>{}</eat:name>'.format(self.supplier['name'])
        message +=      '<eat:supplier>' 
        message +=               '<eat:INN>{}</eat:INN>'.format(self.supplier['inn'])
        message +=               '<eat:KPP>{}</eat:KPP>'.format(self.supplier['kpp'])
        message +=               '<eat:OGRN>{}</eat:OGRN>'.format(self.supplier['ogrn'])
        message +=               '</eat:supplier>'
        message +=          '<eat:contactInfo>'
        message +=              '<eat:email>{}</eat:email>'.format(self.supplier['email'])
        message +=              '<eat:phone>79384306705</eat:phone>'.format(self.supplier['phone'])
        message +=             '</eat:contactInfo>' + \
                          '</eat:SupplierInfo>' + \
                          '<eat:ProposalConfirmation>Да</eat:ProposalConfirmation>' + \
                          '<eat:DeliveryPrice>0</eat:DeliveryPrice>' + \
                      '</OrderProposalInfo>'
        message += '<extSystem>{}</extSystem>'.format(self.ext_system)
        message +='</n1:requestOrderProposal>'
        self.message = message         
        return self.message

    def __call__(self):
        result =  super().__call__()
        if result['processingState'].lower() == "error".lower():
            raise ExceptionBerezkaErrorProposal(f'Предложение с ценой {self.price}  не прошло') 
        else:
            return result     

class requestBerezkaProposalWithoutParser(requestBerezkaBase):
    def __init__(self, token, ext_system, order, price, supplier):
        super().__init__(token, ext_system)
        self.url_request = 'https://agregatoreat.ru/integration/ecom/rest/api/order/orderProposal'
        self.order = order
        self.price = price
        self.supplier = supplier
        self._createMessage()

    def _createMessage(self):
        message = '<?xml version="1.0" encoding="UTF-8"?>' + \
                    '<n1:requestOrderProposal xmlns:eat="http://agregatoreat.ru/eat/" ' + \
                    'xmlns:n1="http://agregatoreat.ru/eat/object-types/" ' + \
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        
        message += 'eat:Version="2.0.0" eat:RequestUID="{}"><referenceOrderInfo>'.format(self.GUID)
        message += '<eat:OrderNumber>{}</eat:OrderNumber>'.format(self.order)
        message +=  '<eat:startDate>0001-01-01T01:00:00.000000</eat:startDate>' + \
                    '<eat:orderExpireDate>0001-01-01T01:00:00.000000</eat:orderExpireDate>' + \
                    '<eat:typePurchase>Закупка до 600 000 руб. (п. 4 ч.1 ст. 93 Закона №44-ФЗ)</eat:typePurchase>' + \
                    '<eat:Product>' + \
                        '<eat:sequenceNumber>1</eat:sequenceNumber>' + \
                        '<eat:EATofferNumber>300932514.000000007_21</eat:EATofferNumber>' + \
                        '<eat:EATClassifierRefCode>28</eat:EATClassifierRefCode>' + \
                        '<eat:name>Оказание услуг по реализации арестованного имущества</eat:name>' + \
                            '<eat:OKEI>' + \
                                '<eat:code>876</eat:code>' + \
                                '<eat:name>УСЛ ЕД</eat:name>' +\
                            '</eat:OKEI>' + \
                            '<eat:OKPD>' + \
                                '<eat:code>68.31.11.110</eat:code>' + \
                                '<eat:name>Услуги посреднические при купле-продаже жилых зданий и занимаемых ими земельных участков за вознаграждение или на договорной основе</eat:name>'+ \
                            '</eat:OKPD>' + \
                            '<eat:availableVolume>1.0</eat:availableVolume>' +\
                            '<eat:homogeneousProductIsPossible>false</eat:homogeneousProductIsPossible>' + \
                    '</eat:Product>'+ \
                    '<eat:Customer>' + \
                        '<eat:CustomerName>МТУ РОСИМУЩЕСТВА В КРАСНОДАРСКОМ КРАЕ И РЕСПУБЛИКЕ АДЫГЕЯ</eat:CustomerName>' + \
                        '<eat:sellerRef>' + \
                            '<eat:INN>2308171570</eat:INN>' +\
                            '<eat:KPP>230901001</eat:KPP>' + \
                            '<eat:OGRN>0000000000000</eat:OGRN>' + \
                        '</eat:sellerRef>' + \
                    '</eat:Customer>' + \
                    '<eat:maxOrderCost>1.00</eat:maxOrderCost>' + \
                    '<eat:PaymentDetails>' + \
                        '<eat:PaymentType>Оплата по счету</eat:PaymentType>'+ \
                        '<eat:PaymentTerms>Отсроченная оплата</eat:PaymentTerms>' + \
                        '<eat:PaymentDeadlineInterval>0</eat:PaymentDeadlineInterval>' + \
                    '</eat:PaymentDetails>' + \
                    '<eat:DeliveryDate>0001-01-01</eat:DeliveryDate>' + \
                    '<eat:remoteService>false</eat:remoteService>' + \
                    '<eat:WWWReference>https://agregatoreat.ru/</eat:WWWReference>' + \
                    '<eat:planDateConclusion>0001-01-01</eat:planDateConclusion>' + \
                    '<eat:gosoboronzakaz>Да</eat:gosoboronzakaz>' + \
                    '<eat:RNP44Flag>Нет</eat:RNP44Flag>' + \
                    '<eat:state>2</eat:state>' + \
                    '<eat:stateDescription>Подача предложений</eat:stateDescription>' + \
                '</referenceOrderInfo>'+ \
                '<OrderProposalInfo>' + \
                    '<eat:productRef>' + \
                        '<eat:refSequenceNumber>1</eat:refSequenceNumber>' + \
                        '<eat:offerCode>300932514.000000007_21</eat:offerCode>'
        message +=      '<eat:unitPrice>{}</eat:unitPrice>'.format(self.price)
        message +=      '<eat:nds>0</eat:nds>' + \
                    '</eat:productRef>' + \
                    '<eat:SupplierInfo>'
        message +=      '<eat:name>{}</eat:name>'.format(self.supplier['name'])
        message +=      '<eat:supplier>'
        message +=          '<eat:INN>{}</eat:INN>'.format(self.supplier['inn'])
        message +=          '<eat:KPP>{}</eat:KPP>'.format(self.supplier['kpp'])
        message +=          '<eat:OGRN>{}</eat:OGRN>'.format(self.supplier['ogrn'])
        message +=       '</eat:supplier>'
        message +=       '<eat:contactInfo>'
        message +=          '<eat:email>{}</eat:email>'.format(self.supplier['email'])
        message +=          '<eat:phone>{}</eat:phone>'.format(self.supplier['phone'])
        message +=       '</eat:contactInfo>'
        message +=   '</eat:SupplierInfo>'+ \
                    '<eat:ProposalConfirmation>Да</eat:ProposalConfirmation>' + \
                    '<eat:DeliveryPrice>0</eat:DeliveryPrice>' + \
                    '</OrderProposalInfo>'
        message +=  '<extSystem>{}</extSystem>'.format(self.ext_system)
        message +=  '</n1:requestOrderProposal>'
        self.message = message         
        return self.message

    def _requestResult(self):
        result = self._request(request_main = False)
        return result

    def __call__(self):
        result =  super().__call__()
        if result['processingState'].lower() == "error".lower():
            raise ExceptionBerezkaErrorProposal(f'Предложение с ценой {self.price}  не прошло')
        elif result['processingState'].lower() == "processing".lower():
            raise ExceptionBerezkaErrorProposal(f'Предложение с ценой {self.price}  прошло, но оно в обработке!')     
        else:
            return result     

class requestBerezkaProposalFake(requestBerezkaProposal):
    def __call__(self):
        logger.debug(f'Тестовая отправка предложения')
        logger.debug(self.message)


def find_order_by_number(order_number):
    MAX_ERROR = 3
    count_error = 0
    while True:
        try:
            order = requestBerezkaOrder(BEREZKA_TOKEN, BEREZKA_EXT_SYSTEM, order_number)
            order_json = order()
            return order_json
        except Exception as ex:
            logger.exception(ex)
            count_error += 1 
            if count_error >= MAX_ERROR:
                raise ex
            else:
                logger.debug(f'Повторный запрос информации о конкурсе на berezka')

def send_proposal(order_json, fake=False):
    MAX_ERROR = 3
    count_error = 0
    while True:
        try:
            if fake:
                proposal = requestBerezkaProposalFake(BEREZKA_TOKEN, BEREZKA_EXT_SYSTEM, order_json["items"][0], BEREZKA_PRICE, SUPPLIER)
            else:
                proposal = requestBerezkaProposal(BEREZKA_TOKEN, BEREZKA_EXT_SYSTEM, order_json["items"][0], BEREZKA_PRICE, SUPPLIER)
            return proposal()
        except Exception as ex:
            logger.exception(ex)
            count_error += 1 
            if count_error >= MAX_ERROR:
                raise ex
            else:
                logger.debug(f'Повторный отправка предложения berezka')


