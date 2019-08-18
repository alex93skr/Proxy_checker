#!/usr/bin/python3
# -*- coding: utf-8 -*-
#############################################################

# proxy checker by skr

#############################################################

import os
import re
import random
import configparser
import json
import threading
import time

import requests
import psycopg2

from psycopg2.extras import DictCursor
from psycopg2 import sql
from bs4 import BeautifulSoup
from fake_headers import Headers


#############################################################

def fake_head():
    return Headers(headers=True).generate()


def scraping_from__free_proxy_list_net(url, limit=1000):
    print('scraping_from__free_proxy_list_net https only:', url, limit)
    proxy_arr = []
    proxy = requests.get(url, headers=fake_head(), timeout=10)
    proxy.encoding = 'utf-8'
    # print(proxy.text)
    count = 0
    https = 0
    if proxy.ok == True:
        proxy = BeautifulSoup(proxy.text, "html.parser")
        try:
            for i in range(1000):
                count += 1
                # print(proxy.tbody('td')[i * 8].text + ':' + proxy.tbody('td')[i * 8 + 1].text, end='')

                if proxy.tbody('td')[i * 8 + 6].text == 'yes':
                    url = proxy.tbody('td')[i * 8].text + ':' + proxy.tbody('td')[i * 8 + 1].text
                    # print(' add')
                    proxy_arr.append(url)
                    https += 1
                    if https == limit:
                        raise Exception
                else:
                    pass
                    # print()
        except:
            pass
    print('proxy scraped:', count, ', added to the list:', len(proxy_arr))
    return proxy_arr


def scraping_from__spys_me(url, limit=1000):
    print('scraping_from__spys_me:', url, limit)
    proxy_arr = []
    proxy = requests.get(url, headers=fake_head(), timeout=10)
    if proxy.ok == True:
        # print(proxy.text)
        proxy_arr = re.findall(r'(?:[0-9]{1,3}[\.]){3}[0-9]{1,3}:\d{1,}', proxy.text)
        # print(proxy_arr)
    print('proxy scraped:', len(proxy_arr), ', added to the list:', len(proxy_arr[:limit]))
    return proxy_arr[:limit]


def check_proxy(proxy):
    url = 'https://yandex.ru/images/'
    proxy1 = {'https': 'https://' + proxy}
    # print(' - proxy_check', proxy, end='')
    try:
        test = requests.get(url, proxies=proxy1, headers=fake_head(), timeout=CHECK_TIMEOUT)
        if test.ok:
            lockprint.acquire()
            print(' - proxy_check', proxy, 'ok')
            lockprint.release()

            return True
    except Exception as err:
        lockprint.acquire()
        print(' - proxy_check', proxy, 'err', err)
        lockprint.release()
        return False


def db_save_value(arr):
    with conn.cursor() as cursor:
        insert = sql.SQL('INSERT INTO proxy (ip) VALUES ({})').format(sql.SQL('),(').join(map(sql.Literal, arr)))
        cursor.execute(insert)
        conn.commit()
        print('insert', len(arr), 'values into db')


def db_del_all_value():
    with conn.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM proxy")
        conn.commit()
        count = cursor.fetchone()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM proxy")
        conn.commit()
    print('del all', count[0], 'values from db')


def db_load_value():
    pass


def db_validation():
    pass


def random_proxy_from_db(arr):
    with conn.cursor() as cursor:
        cursor.execute("select ip from proxy limit 1 offset floor(random() * (select count(*) from proxy));")
        conn.commit()
        proxy = cursor.fetchone()
    return proxy[0]


class MyThread(threading.Thread):

    def __init__(self, ip):
        self.ip = ip
        """Инициализация потока"""
        threading.Thread.__init__(self)

    def run(self):
        if check_proxy(self.ip):
            lockarr.acquire()
            proxy_list_good.append(self.ip)
            lockarr.release()


def main():
    global proxy_list_not_checked

    # proxy_list_not_checked += scraping_from__free_proxy_list_net('https://free-proxy-list.net', limit=MAX_PROXY_COUNT)
    # proxy_list_not_checked += scraping_from__free_proxy_list_net('https://www.us-proxy.org', limit=MAX_PROXY_COUNT)
    # proxy_list_not_checked += scraping_from__free_proxy_list_net('https://free-proxy-list.net/uk-proxy.html')
    proxy_list_not_checked += scraping_from__spys_me('http://spys.me/proxy.txt', limit=MAX_PROXY_COUNT)

    print(len(proxy_list_not_checked))

    for i in proxy_list_not_checked:
        t = MyThread(i)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(threading.enumerate())

    print(len(proxy_list_good))
    # print(proxy_list_good)

    if len(proxy_list_good) > 10:
        db_del_all_value()
        db_save_value(proxy_list_good)

    # db_validation()
    # db_load_value()

    # scraping
    # parsing


#############################################################


if __name__ == "__main__":

    if "HEROKU" in list(os.environ.keys()):
        host = os.environ['host']
        database = os.environ['database']
        user = os.environ['user']
        password = os.environ['password']
    else:
        config = configparser.ConfigParser()
        config.read('proxy_checker.ini')
        host = config.get('Settings', 'host')
        database = config.get('Settings', 'database')
        user = config.get('Settings', 'user')
        password = config.get('Settings', 'password')

    lockarr = threading.Lock()
    lockprint = threading.Lock()

    threads = []
    proxy_list_not_checked = []
    proxy_list_good = []

    MAX_PROXY_COUNT = 1000
    CHECK_TIMEOUT = 2
    run = 0

    while True:
        try:
            conn = psycopg2.connect(dbname=database, user=user, password=password, host=host, sslmode='require')
            print('connect to postgres OK')
            main()
            conn.close()
            run += 1
            print('script is runing ', run, 'times')
            print('sleep ...')
            time.sleep(3600)  # спать час
        except Exception as err:
            print('mainERR:', err)
            print('script is runing ', run, 'times')
            print('sleep ...')
            time.sleep(3600)  # спать час

#############################################################
