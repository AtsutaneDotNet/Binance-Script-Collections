import ccxt

api_key = ""
secret_key = ""
margin_type = "ISOLATED"
leverage = 11

def changeMarginLev():
    print("Margin Type Setting: "+margin_type)
    print("Leverage Setting: "+str(leverage))
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': secret_key,
        'timeout': 30000,
        'enableRateLimit': True,
        'option': {'defaultMarket': 'futures'},
        'urls': {
            'api': {
                'public': 'https://fapi.binance.com/fapi/v1',
                'private': 'https://fapi.binance.com/fapi/v1',
            }, }
    })
    print("Get coin/token list from "+exchange_id)
    get_list = exchange.fapiPublicGetTickerPrice()
    print("Processing coin/token list")
    for data in get_list:
        print("Processing "+data['symbol'])
        try:
            response = exchange.fapiPrivate_post_margintype({
                 'symbol': data['symbol'],
                 'marginType': margin_type,
            })
        except Exception as e:
            response = str(e)
        print("Margin Type: "+str(response))
        try:
            response = exchange.fapiPrivate_post_leverage({
                'symbol': data['symbol'],
                'leverage': leverage,
            })
        except Exception as e:
            response = str(e)
        print("Leverage: "+str(response))
    print("Finish processing coin/token list")

changeMarginLev()
