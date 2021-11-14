from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
import time
import threading
import os
import json
import sqlite3
import datetime
from sqlite3 import OperationalError
from colorama import init
from colorama import Fore,Style,Back

init(autoreset=True)

database = "database/liquidation.db"

def create():
    conn = sqlite3.connect(database, timeout=15)
    c = conn.cursor()
    c.execute('CREATE TABLE liquidation (coin text, price integer, qty integer, size integer, side text, time integer UNIQUE)')
    conn.commit()
    conn.close()

def read_db():
    try:
        conn = sqlite3.connect(database, timeout=15)
        c = conn.cursor()
        c.execute('SELECT * FROM  liquidation')
        data = c.fetchall()
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        create()

def cleanup_db():
    conn = sqlite3.connect(database, timeout=15)
    c = conn.cursor()
    now = datetime.datetime.utcnow()
    yday = now - datetime.timedelta(days = 1)
    yts = yday.timestamp() * 1000
    times = now.strftime("%m/%d/%Y %H:%M:%S")
    print("[" + Fore.CYAN + times + Fore.WHITE + "] Performing DB Cleanup On " + Fore.GREEN + "tracker.DB")
    c.execute('DELETE FROM liquidation WHERE time < ?', (yts,)).fetchall()
    conn.commit()
    conn.close()

def websocket_worker(binance_websocket_api_manager):
    now = datetime.datetime.utcnow()
    times = now.strftime("%m/%d/%Y %H:%M:%S")
    print("[" + Fore.CYAN + times + Fore.WHITE + "] Checking For Liquidation Data on " + Fore.GREEN + "USD-M Binance Future")
    time.sleep(30)
    while True:
        if binance_websocket_api_manager.is_manager_stopping():
            exit(0)
        liqdata = binance_websocket_api_manager.pop_stream_data_from_stream_buffer("liquidation")
        if liqdata is False:
            time.sleep(0.01)
        else:
            try:
                # remove # to activate the print function:
                rawliq = json.loads(liqdata)
                dbdata = json.loads(json.dumps(rawliq['o']))
                liqname = dbdata['s']
                if "_" not in liqname and "BUSD" != liqname[-4:]:
                    liqname = liqname.replace("USDT","")
                    liqside = dbdata['S']
                    liqprice = float(dbdata['p'])
                    liqqty = round(float(dbdata['q']),4)
                    liqsize = round(liqqty * liqprice,0)
                    liqtime = int(dbdata['T'])
                    #read Current Data in DB
                    conn = sqlite3.connect(database, timeout=15)
                    c = conn.cursor()
                    timetoshow = liqtime / 1000
                    timetoshow = datetime.datetime.utcfromtimestamp(timetoshow).strftime('%m/%d/%Y %H:%M:%S')
                    print("[" + Fore.CYAN + timetoshow + Fore.WHITE + "] " + Fore.RED + liqname + Fore.WHITE + " liquidation found for " + Fore.YELLOW + str(liqqty) + Fore.WHITE + " worth " + Fore.GREEN + "$" + str(liqsize))
                    #Delete Existting Data when updating
                    try:
                        c.execute('INSERT OR REPLACE INTO liquidation VALUES (?, ?, ?, ?, ?, ?)',
                                  (liqname, liqprice, liqqty, liqsize, liqside, liqtime))
                        conn.commit()
                        conn.close()
                    except OperationalError as e:
                        print("Error In line 2 "+str(e))
                        #read_db()
                    except IndexError:
                        c.execute('INSERT OR REPLACE INTO liquidation VALUES (?, ?, ?, ?, ?, ?)',
                                  (liqname, liqprice, liqqty, liqsize, liqside, liqtime))
                        conn.commit()
                        conn.close()
                else:
                    pass
            except KeyError:
                # Any kind of error...
                # not able to process the data? write it back to the stream_buffer
                binance_websocket_api_manager.add_to_stream_buffer(liqdata)

if __name__ == '__main__':
    read_db()
    binance_websocket_api_manager = BinanceWebSocketApiManager(exchange="binance.com-futures")
    worker_thread = threading.Thread(target=websocket_worker, args=(binance_websocket_api_manager,))
    worker_thread.start()
    liquidation_stream_id = binance_liquidation = binance_websocket_api_manager.create_stream(["!forceOrder"], "arr", stream_buffer_name="liquidation")
    try:
        while True:
            cleanup_db()
            time.sleep(86400)
    except KeyboardInterrupt:
        print("Stopping ... just wait a few seconds!")
        binance_websocket_api_manager.stop_manager_with_all_streams()
