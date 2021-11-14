from flask import Flask, render_template, jsonify, Markup, redirect, url_for, request
import ccxt
import sqlite3
import datetime
from urllib.request import urlopen,Request
import json
import random
import numpy
from scipy import stats
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

liq_db = "database/liquidation.db"

#Rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per minute", "50 per second"]
)

@app.route("/")
def index():
    now = datetime.datetime.utcnow()
    yday = now - datetime.timedelta(days = 1)
    yts = yday.timestamp() * 1000
    conn = sqlite3.connect(liq_db, timeout=15)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    datas = c.execute('SELECT coin,count(coin),sum(size) FROM liquidation WHERE time >= ? GROUP BY coin', (yts,)).fetchall()
    conn.commit()
    conn.close()
    data_table = {}
    list_table = []
    for data in datas:
        small_list = {}
        small_list.update({"name":data[0]})
        small_list.update({"lick_amount":data[1]})
        small_list.update({"lick_value":data[2]})
        conn = sqlite3.connect(liq_db, timeout=15)
        conn.row_factory = lambda cursor, row: row[0]
        c = conn.cursor()
        lastliq = c.execute('SELECT time FROM liquidation WHERE coin = ? ORDER BY time DESC', (data[0],)).fetchone()
        lick_value = c.execute('SELECT size FROM liquidation WHERE time >= ? AND coin = ?', (yts,data[0],)).fetchall()
        conn.commit()
        conn.close()
        mode_data = stats.mode(lick_value)
        small_list.update({"mean_value":round(numpy.mean(lick_value))})
        small_list.update({"median_value":round(numpy.median(lick_value))})
        small_list.update({"mode_value":round(mode_data[0][0])})
        small_list.update({"last_liquidation":lastliq})
        list_table.append(small_list)
    data_table.update({"data":list_table})
    output = jsonify(data_table)
    return output

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=80, debug=False)
