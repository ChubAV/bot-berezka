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