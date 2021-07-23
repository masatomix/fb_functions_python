#!/usr/bin/python
import socket
import sys
from time import time
import time as t
import base64

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

import configparser

from google.cloud import logging
from google.cloud.logging import DESCENDING

import pandas as pd
from pandas import DataFrame


inifile = configparser.ConfigParser()
inifile.read('./config.ini', 'UTF-8')


def execute(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)

    vpn_server = inifile.get('vpn', 'vpn_server')
    vpn_port = inifile.getint('vpn', 'vpn_port')
    checkserver(vpn_server, vpn_port)


def execute1(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)
    _list_entries()


def get_count_message():
    # Pythonのサンプルコード
    # https://github.com/googleapis/python-logging/blob/master/samples/snippets/usage_guide.py
    """Lists the most recent entries for a given logger."""
    logger_name = "cloudfunctions.googleapis.com%2Fcloud-functions"
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)

    # https://cloud.google.com/logging/docs/view/advanced-queries
    # 検索条件指定方法
    filter_str = 'resource.type="cloud_function" AND resource.labels.function_name="vpn-check" AND resource.labels.region = "asia-northeast1" AND textPayload:"回目"'
    page_size = 200
    entries = []
    for i, entry in enumerate(logger.list_entries(filter_=filter_str, page_size=page_size, order_by=DESCENDING)):
        # timestamp = entry.timestamp.isoformat()
        # print("* {}: {}".format(timestamp, entry.payload))
        entries.append(entry)
        if i == page_size-1:
            break

    # pd.set_option('display.max_columns', 50)
    df = DataFrame(entries)
    # df.to_csv('log_kaime.csv')

    df['timestamp'] = pd.to_datetime(
        df['timestamp'], utc=True).dt.tz_convert('Asia/Tokyo')
    df['count'] = 1
    df_groupby = df.groupby('payload')['count'].count()
    return df_groupby.to_csv(sep='\t')


def _list_entries():
    # Pythonのサンプルコード
    # https://github.com/googleapis/python-logging/blob/master/samples/snippets/usage_guide.py
    """Lists the most recent entries for a given logger."""
    logger_name = "cloudfunctions.googleapis.com%2Fcloud-functions"
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)

    print("Listing entries for logger {}:".format(logger.name))

    # https://cloud.google.com/logging/docs/view/advanced-queries
    # 検索条件指定方法
    filter_str = 'severity=DEBUG AND resource.type="cloud_function" AND resource.labels.function_name="vpn-check" AND resource.labels.region = "asia-northeast1"  AND textPayload:"Function execution took"'
    page_size = 200
    entries = []
    for i, entry in enumerate(logger.list_entries(filter_=filter_str, page_size=page_size, order_by=DESCENDING)):
        # timestamp = entry.timestamp.isoformat()
        # print("* {}: {}".format(timestamp, entry.payload))
        entries.append(entry)
        if i == page_size-1:
            break

    # pd.set_option('display.max_columns', 50)
    df = DataFrame(entries)
    df['timestamp'] = pd.to_datetime(
        df['timestamp'], utc=True).dt.tz_convert('Asia/Tokyo')
    df.index = df['timestamp']
    df['count'] = 1

    df_ok = df[df['payload'].str.contains('ok')]
    df_ok_groupby = df_ok.groupby(
        pd.Grouper(key='timestamp', freq='1h'))['count'].count()
    print(df_ok_groupby.to_csv(sep='\t'))

    df_crashed = df[df['payload'].str.contains('crashed')]
    df_crashed_groupby = df_crashed.groupby(
        pd.Grouper(key='timestamp', freq='1h'))['count'].count()
    print(df_crashed_groupby.to_csv(sep='\t'))

    # for entry in entries:
    #     timestamp = entry.timestamp.isoformat()
    #     print("* {}: {}".format(timestamp, entry.payload))
    # from dateutil import tz
    # JST = tz.gettz('Asia/Tokyo')
    # entriesStrArray = ["{0}: {1}".format(
    #     entry.timestamp.astimezone(JST).isoformat(), entry.payload) for entry in entries]
    # entriesStrArray.insert(0, '定期バッチの実行状況です。直近のOK件数を表示しています')
    # message = '\n'.join(entriesStrArray)
    messages = ['定期バッチの実行状況です。直近のOK件数:',
                df_ok_groupby.to_csv(sep='\t'),
                '定期バッチの実行状況です。直近のNG件数:',
                df_crashed_groupby.to_csv(sep='\t'),
                '\n直近200回のうち、リトライ回数(0回目が基本で、それ以外は原則はないはず):',
                get_count_message(),
                ]
    message = '\n'.join(messages)
    print(message)
    sendMail('定期バッチの実行状況(直近の実行結果)', message)


senddata = b"\x38\x01\x00\x00\x00\x00\x00\x00\x00"


def _checkserver(ip, port):
    print('Checking %s:%s' % (ip, port))  # <------
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # in seconds
    time_start = time()
    sock.connect((ip, int(port)))
    print("Sending request...")  # <------
    sock.send(senddata)
    message = ""
    tmpE: Exception = None
    try:
        dta = sock.recv(100)
        time_end = time()
        message = "サーバへの接続に成功しました({0}:{1}) : {2:.4f} sec response time.".format(
            ip, port, time_end - time_start)
        print(message)
    except Exception as e:
        message = "サーバへの接続に失敗しました({0}:{1}) ".format(ip, port)
        print(message)
        tmpE = e
    finally:
        sock.close()
    return tmpE, message


def checkserver(ip, port):
    debugFlag = inifile.getboolean('debug', 'debug')
    interval = inifile.getfloat('retry', 'interval')
    try_count = inifile.getint('retry', 'try_count')
    for index in range(try_count):
        print(f'{index}回目')
        retE, message = _checkserver(ip, port)
        if retE is None:
            if debugFlag:
                sendMail('疎通成功', message)
            return 0
        else:
            if index == try_count-1:
                sendMail('疎通失敗', message)
                raise retE
            else:
                # print(f'{interval}秒まち')
                t.sleep(interval)  # 3秒待って、for文を終える
                # print(f'{interval}秒まち終わり')


def createSMTPObj(smtp, port, user, password):
    smtpobj = smtplib.SMTP(smtp, port)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(user, password)
    return smtpobj


def createMessageObj(subject, from_address, to_address, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Date'] = formatdate()
    return msg


def sendMail(subject, message, to_addr=inifile.get('mail', 'to_addr')):
    from_addr = inifile.get('mail', 'from_addr')
    password = inifile.get('mail', 'password')
    smtp_server = inifile.get('mail', 'smtp_server')
    smtp_port = inifile.getint('mail', 'smtp_port')
    smtpobj = createSMTPObj(smtp_server, smtp_port, from_addr, password)
    msg = createMessageObj(subject, from_addr, to_addr, message)

    smtpobj.sendmail(from_addr, to_addr, msg.as_string())
    smtpobj.close()


def main():
    argvs = sys.argv
    argc = len(argvs)

    if(argc == 3):
        checkserver(argvs[1], argvs[2])
    else:
        vpn_server = inifile.get('vpn', 'vpn_server')
        vpn_port = inifile.getint('vpn', 'vpn_port')
        checkserver(vpn_server, vpn_port)


if __name__ == "__main__":
    main()


# from flask import escape

# def hello_http1(request):
#     """HTTP Cloud Function.
#     Args:
#         request (flask.Request): The request object.
#         <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
#     Returns:
#         The response text, or any set of values that can be turned into a
#         Response object using `make_response`
#         <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
#     """
#     request_json = request.get_json(silent=True)
#     request_args = request.args

#     if request_json and 'name' in request_json:
#         name = request_json['name']
#     elif request_args and 'name' in request_args:
#         name = request_args['name']
#     else:
#         name = 'World'
#     return 'Hello {}!'.format(escape(name))
