import ccxt
import json
from pprint import pprint
from time import sleep
import win32api

api_key = ""
secret_key = ""
MaxOpen = 2
coins = "coins.json"
current_position = ""

def getJsonFile(file):
    with open(file) as f:
        data = json.load(f)
    return data

def writeJsonFile(file,data):
    with open(file, 'w') as outfile:
        json.dump(data, outfile, indent=4)

pprint("Backup existing coin.json inside variable")
load_coin = getJsonFile(coins)

def exitScript(signal_type):
    pprint("Restore back original coins.json")
    writeJsonFile(coins,load_coin)

win32api.SetConsoleCtrlHandler(exitScript, True)

#pprint(load_coin)

def MaxPos():
    global current_position
    output = []
    pprint("Fetching open position from Binance")
    exchange_class = getattr(ccxt, 'binance')
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': secret_key,
        'timeout': 30000,
        'enableRateLimit': True,
        'option': {'defaultMarket': 'futures'}
    })
    accountInfo = exchange.fapiPrivateGetAccount()
    open_position = []
    for post in accountInfo['positions']:
        if float(post['initialMargin']) > 0:
            open_position.append(post['symbol'].replace("USDT",""))
    OpenOrder = len(open_position)
    show_positions = ",".join(map(str, open_position))
    pprint("Found "+str(OpenOrder)+" open positions: "+show_positions)
    if OpenOrder >= MaxOpen:
        pprint("Max Open Activated")
        if current_position != open_position:
            for coin in load_coin:
                if coin['symbol'] in open_position:
                    output.append(coin)
            pprint(output)
            writeJsonFile(coins,output)
            current_position = open_position
        else:
            pass
    else:
        pprint("Max Open Deactivated")
        writeJsonFile(coins,load_coin)

if __name__ == '__main__':
    pprint("Start Managing Max Pos Loop")
    try:
        while True:
            MaxPos()
            pprint("Sleep for 15 seconds")
            sleep(15)
    except KeyboardInterrupt:
        pprint("Restore back original coins.json")
        writeJsonFile(coins,load_coin)
