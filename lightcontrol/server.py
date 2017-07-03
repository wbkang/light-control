#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import threading
import logging
from tzlocal import get_localzone
from flask import Flask, render_template, url_for, request, make_response
from lightcontrol.config import lights

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s')
GPIO.setmode(GPIO.BCM)
logger = logging.getLogger(__name__)

app = Flask("lightcontrol")

def toggle_switch(light_name, onoff):
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


#import IPython
#IPython.embed()
