#! /usr/bin/env python
# -*- coding:utf-8 -*-


import time
import json
from websocket import create_connection

# pip install websocket-client
ws = ""

def takeAction(action, data):
    if action == "__bet":
        #time.sleep(2)
        ws.send(json.dumps({
            "eventName": "__action",
            "data": {
                "action": "bet",
                "playerName": "player1",
                "amount": 100
            }
        }))
    elif action == "__action":
        #time.sleep(2)
        ws.send(json.dumps({
            "eventName": "__action",
            "data": {
                "action": "call",
                "playerName": "player1"
            }
        }))


def doListen():
    try:
        global ws
        ws = create_connection("ws://poker-dev.wrs.club:3001")
        ws.send(json.dumps({
            "eventName": "__join",
            "data": {
                "playerName": "player1"
            }
        }))
        while 1:
            result = ws.recv()
            msg = json.loads(result)
            event_name = msg["eventName"]
            data = msg["data"]
            print event_name
            print data
            takeAction(event_name, data)
    except Exception, e:
        print e
        #doListen()


if __name__ == '__main__':
    doListen()
