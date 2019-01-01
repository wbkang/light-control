#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading
import logging
from threading import RLock, Lock, Thread
from tzlocal import get_localzone
from flask import Flask, render_template, url_for, request, make_response
from lightcontrol.config import lights
from os.path import expanduser
import os.path
import json

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s')
GPIO.setmode(GPIO.BCM)
logger = logging.getLogger(__name__)

app = Flask("lightcontrol")

home_dir = expanduser('~')

class Preferences:
    def __init__(self, filename):
        self.filename = filename
        self.lock = RLock()
    def read(self):
        with self.lock:
            if os.path.exists(self.filename):
                try:
                    with open(self.filename, 'rb') as f:
                        return json.loads(f.read().decode('utf-8'))
                except:
                    logger.exception("Error reading JSON. Resetting preferences")
                    return dict()
            else:
                return dict()
    def write(self, d):
        with self.lock:
            with open(self.filename, 'wb') as f:
                return f.write(json.dumps(d).encode('utf-8'))
    def update(self, key, value):
        with self.lock:
            p = self.read()
            p[key] = value
            self.write(p)

pref = Preferences(filename=home_dir + '/.lightcontrol')

switch_lock = Lock()

def toggle_switch(light_name, onoff):
    with switch_lock:
        pref.update(light_name, onoff)
        line = lights[light_name][0 if onoff else 1]
        GPIO.setup(line, GPIO.OUT)
        GPIO.output(line, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(line, GPIO.LOW)

@app.route("/")
def index():
    return render_template("index.html", config=lights)

@app.route("/lights/<room_name>/<onoff>", methods=["POST"])
def control(room_name, onoff):
    onoff = onoff == "on"
    toggle_switch(room_name, onoff)
    return make_response(str(onoff), 200)

@app.route("/lights/<room_name>/status", methods=["GET"])
def status(room_name):
    stat = pref.read().get(room_name, False)
    # update
    #toggle_switch(room_name, stat)
    return "1" if stat else "0"

def poll_sqs():
    import boto3
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/865135545601/alexa-light.fifo'
    logger.info("sqs polling thread start") 
    while True:
        logger.info("sqs polling!") 
        response = sqs.receive_message(
                QueueUrl=queue_url,
                AttributeNames=[
                            'SentTimestamp'
                        ],
                MaxNumberOfMessages=1,
                MessageAttributeNames=[
                            'All'
                        ],
                VisibilityTimeout=1,
                WaitTimeSeconds=20
        )
        if response.get('Messages'):
            logger.info("Got responses: %d" % len(response['Messages'])) 
            for message in response['Messages']:
                r = json.loads(message['Body'])['request']['directive']
                onoff = r['header']['name'] == 'TurnOn'
                light_name = r['endpoint']['endpointId']
                logger.info("From SQS, toggle: %s, %s" % (light_name, onoff))
                toggle_switch(light_name, onoff)
                receipt_handle = message['ReceiptHandle']
                logger.info("Deleting message %r" % receipt_handle)
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
        else:
            logger.info("No messages")

sqs_thread = Thread(target=poll_sqs)
sqs_thread.start()

#for name, val in pref.read().items():
#    toggle_switch(name, val)

#import IPython
#IPython.embed()
