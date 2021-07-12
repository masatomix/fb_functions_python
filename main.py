#!/usr/bin/python
import socket
import sys
from time import time
import base64

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

import configparser

inifile = configparser.ConfigParser()
inifile.read('./config.ini', 'UTF-8')


def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)

    vpn_server = inifile.get('vpn', 'vpn_server')
    vpn_port = inifile.get('vpn', 'vpn_port')
    checkserver(vpn_server, vpn_port)


senddata = b"\x38\x01\x00\x00\x00\x00\x00\x00\x00"


def checkserver(ip, port):
    print('Checking %s:%s' % (ip, port))  # <------
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)  # in seconds
    time_start = time()
    sock.connect((ip, int(port)))
    print("Sending request...")  # <------
    sock.send(senddata)
    message = ""
    try:
        dta = sock.recv(100)
        time_end = time()
        message = "OpenVPN({0}:{1}) Connection OK : {2:.4f} sec response time.".format(
            ip, port, time_end - time_start)
        print(message)
        sendMail('疎通成功', message)
    except:
        message = "OpenVPN({0}:{1}) Connection failed.".format(ip, port)
        print(message)
        sendMail('疎通失敗', message)
    sock.close()
    return message


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


def sendMail(subject, message):
    to_addr = inifile.get('mail', 'to_addr')
    from_addr = inifile.get('mail', 'from_addr')
    password = inifile.get('mail', 'password')
    smtp_server = inifile.get('mail', 'smtp_server')
    smtp_port = inifile.get('mail', 'smtp_port')
    smtpobj = createSMTPObj(smtp_server, smtp_port, from_addr, password)
    msg = createMessageObj(subject, from_addr, to_addr, message)

    smtpobj.sendmail(from_addr, to_addr, msg.as_string())
    smtpobj.close()


def main():
    argvs = sys.argv
    argc = len(argvs)

    if(argc == 3):
        print(checkserver(argvs[1], argvs[2]))
    else:
        vpn_server = inifile.get('vpn', 'vpn_server')
        vpn_port = inifile.get('vpn', 'vpn_port')
        print(checkserver(vpn_server, vpn_port))


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
